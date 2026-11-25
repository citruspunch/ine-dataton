"""Lectura y normalización de las hojas de la Canasta Básica Alimentaria."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from .errors import IngestError
from .months import month_name, month_number, period

DAYS_PER_MONTH = 30
REFERENCE_KCAL: dict[str, float] = {"Urbana": 2052.0, "Rural": 2172.0}

_ZERO_KCAL_TOLERANCE = 1e-9


def _normalize(text: object) -> str:
    value = unicodedata.normalize("NFKD", str(text))
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", value.strip().lower())


def _pick_column(frame: pd.DataFrame, expected: str, *, context: str) -> str:
    """Busca una columna por nombre normalizado (sin acentos ni mayúsculas)."""
    wanted = _normalize(expected)
    for column in frame.columns:
        if _normalize(column) == wanted:
            return str(column)
    available = ", ".join(repr(str(c)) for c in frame.columns)
    raise IngestError(
        f"{context}: falta la columna {expected!r}. Columnas disponibles: {available}"
    )


def _read_sheet(path: Path, sheet: int | str, *, context: str) -> pd.DataFrame:
    try:
        frame = pd.read_excel(path, sheet_name=sheet, header=0, engine="calamine")
    except Exception as exc:  # noqa: BLE001
        raise IngestError(f"{context}: no fue posible leer {path.name}: {exc}") from exc
    frame = frame.dropna(how="all")
    if frame.empty:
        raise IngestError(f"{context}: la hoja {sheet!r} está vacía en {path.name}")
    return frame


def _months(frame: pd.DataFrame, *, context: str) -> pd.DataFrame:
    year_col = _pick_column(frame, "Año", context=context)
    month_col = _pick_column(frame, "Mes", context=context)
    out = frame.copy()
    out["year"] = pd.to_numeric(out[year_col], errors="coerce").astype("Int64")
    if out["year"].isna().any():
        raise IngestError(f"{context}: hay filas sin año válido")
    out["month"] = [month_number(value) for value in out[month_col]]
    out["month_name"] = [month_name(value) for value in out["month"]]
    out["period"] = [period(y, m) for y, m in zip(out["year"], out["month"], strict=True)]
    return out


def read_percapita_costs(path: Path, area: str) -> pd.DataFrame:
    """Hoja de costo diario y mensual per cápita de la CBA (una fila por mes)."""
    context = f"CBA {area} · costos per cápita"
    raw = _read_sheet(path, 0, context=context)
    frame = _months(raw, context=context)

    daily_col = (
        _pick_column(frame, "Costo diario (Per cápita Q)", context=context)
        if (area == "Urbana")
        else _pick_column(frame, "Costo diario Per cápita (Q)", context=context)
    )
    published_col = _pick_column(frame, "Costo mensual Per cápita (Q)", context=context)

    frame["daily_cost"] = pd.to_numeric(frame[daily_col], errors="coerce")
    frame["published_monthly_cost"] = pd.to_numeric(frame[published_col], errors="coerce")
    frame = frame.dropna(subset=["daily_cost"]).copy()
    frame["monthly_cost"] = frame["daily_cost"] * DAYS_PER_MONTH
    frame["area"] = area

    if (frame["daily_cost"] <= 0).any():
        raise IngestError(f"{context}: hay costos diarios no positivos")
    duplicates = frame.duplicated(subset=["year", "month"])
    if duplicates.any():
        raise IngestError(f"{context}: periodos duplicados")

    columns = [
        "area",
        "year",
        "month",
        "month_name",
        "period",
        "daily_cost",
        "monthly_cost",
        "published_monthly_cost",
    ]
    return frame[columns].sort_values(["year", "month"], ignore_index=True)


def read_products(path: Path, area: str) -> pd.DataFrame:
    """Hoja de productos: kcal, gramos y costo diario/mensual por producto."""
    context = f"CBA {area} · productos"
    raw = _read_sheet(path, 1, context=context)
    frame = _months(raw, context=context)

    columns = {
        "product": "Producto",
        "base_quantity": "Cantidad base",
        "base_unit": "Unidad de medida base",
        "kcal_daily": "Kilocalorías diarias",
        "kcal_monthly": "Kilocalorías mensuales",
        "grams_daily": "Cantidad gramos diarios",
        "grams_monthly": "Cantidad gramos mensuales",
        "cost_daily": "Costo diario",
        "cost_monthly": "Costo mensual",
        "unit_price": "Precio según unidad de medida base",
    }
    for target, label in columns.items():
        source = _pick_column(frame, label, context=context)
        frame[target] = frame[source]

    for numeric in (
        "base_quantity",
        "kcal_daily",
        "kcal_monthly",
        "grams_daily",
        "grams_monthly",
        "cost_daily",
        "cost_monthly",
        "unit_price",
    ):
        frame[numeric] = pd.to_numeric(frame[numeric], errors="coerce")

    frame["product"] = frame["product"].astype(str).str.strip()
    frame["base_unit"] = frame["base_unit"].astype(str).str.strip()
    frame["area"] = area

    if frame[["product", "kcal_daily", "cost_daily", "unit_price"]].isna().any().any():
        raise IngestError(f"{context}: hay valores numéricos o nombres vacíos")
    if frame.duplicated(subset=["year", "month", "product"]).any():
        raise IngestError(f"{context}: producto duplicado dentro de un mismo mes")

    frame["zero_kcal"] = frame["kcal_daily"].abs() <= _ZERO_KCAL_TOLERANCE
    frame["cost_per_1000_kcal"] = (
        frame["cost_daily"] / frame["kcal_daily"].where(~frame["zero_kcal"]) * 1000.0
    )

    ordered = [
        "area",
        "year",
        "month",
        "month_name",
        "period",
        "product",
        "base_quantity",
        "base_unit",
        "unit_price",
        "kcal_daily",
        "kcal_monthly",
        "grams_daily",
        "grams_monthly",
        "cost_daily",
        "cost_monthly",
        "cost_per_1000_kcal",
        "zero_kcal",
    ]
    return frame[ordered].sort_values(["year", "month"], ignore_index=True)


def read_groups(path: Path, area: str) -> pd.DataFrame:
    """Hoja de grupos alimenticios publicada por el INE."""
    context = f"CBA {area} · grupos"
    raw = _read_sheet(path, 0, context=context)
    frame = _months(raw, context=context)

    columns = {
        "group": "Grupo alimenticio",
        "kcal_daily": "Kilocalorías diarias",
        "kcal_monthly": "Kilocalorías mensuales",
        "grams_daily": "Cantidad gramos diarios",
        "grams_monthly": "Cantidad gramos mensuales",
        "cost_daily": "Costo diario",
        "cost_monthly": "Costo mensual",
    }
    for target, label in columns.items():
        frame[target] = frame[_pick_column(frame, label, context=context)]

    for numeric in (
        "kcal_daily",
        "kcal_monthly",
        "grams_daily",
        "grams_monthly",
        "cost_daily",
        "cost_monthly",
    ):
        frame[numeric] = pd.to_numeric(frame[numeric], errors="coerce")
    frame["group"] = frame["group"].astype(str).str.strip()
    frame["area"] = area
    frame["cost_per_1000_kcal"] = (
        frame["cost_daily"] / frame["kcal_daily"].where(frame["kcal_daily"] > 0) * 1000.0
    )

    ordered = [
        "area",
        "year",
        "month",
        "month_name",
        "period",
        "group",
        "kcal_daily",
        "kcal_monthly",
        "grams_daily",
        "grams_monthly",
        "cost_daily",
        "cost_monthly",
        "cost_per_1000_kcal",
    ]
    return frame[ordered].sort_values(["year", "month"], ignore_index=True)


@dataclass(slots=True)
class CbaBundle:
    area: str
    costs: pd.DataFrame
    products: pd.DataFrame
    groups: pd.DataFrame
    product_groups: pd.DataFrame
    reference_kcal: float
    max_group_cost_gap: float
    zero_kcal_products: list[str] = field(default_factory=list)

    @property
    def periods(self) -> list[str]:
        return sorted(self.costs["period"].unique().tolist())


def assign_product_groups(
    products: pd.DataFrame,
    groups: pd.DataFrame,
    *,
    area: str,
) -> tuple[pd.DataFrame, float]:
    """Asigna cada producto a su grupo alimenticio.

    La hoja de productos del INE no incluye el grupo, pero sus filas están
    ordenadas por grupo y la kcal diaria de cada grupo es la suma exacta de sus
    productos. Se recorre cada mes acumulando kcal hasta cerrar el total del
    grupo; luego se valida que cada producto caiga siempre en el mismo grupo en
    los 34 meses y se mide la diferencia de costo contra la hoja de grupos.
    """
    mapping: dict[str, str] = {}
    max_gap = 0.0

    for (year, month), chunk in products.groupby(["year", "month"], sort=True):
        rows = chunk.reset_index(drop=True)
        targets = groups[(groups["year"] == year) & (groups["month"] == month)].reset_index(
            drop=True
        )
        if targets.empty:
            raise IngestError(f"CBA {area}: no hay grupos para {year}-{month:02d}")

        accumulated = 0.0
        group_index = 0
        assigned: list[str] = []
        for kcal in rows["kcal_daily"]:
            accumulated += float(kcal)
            assigned.append(str(targets.loc[group_index, "group"]))
            if (
                group_index < len(targets)
                and abs(accumulated - float(targets.loc[group_index, "kcal_daily"])) <= 1e-6
            ):
                accumulated = 0.0
                group_index += 1

        if group_index != len(targets) or abs(accumulated) > 1e-6:
            raise IngestError(
                f"CBA {area}: no se pudo reconstruir la agrupación de {year}-{month:02d}; "
                "la hoja de productos ya no cierra contra la hoja de grupos."
            )

        for name, group in zip(rows["product"], assigned, strict=True):
            previous = mapping.setdefault(str(name), group)
            if previous != group:
                raise IngestError(
                    f"CBA {area}: el producto {name!r} aparece en {previous!r} y {group!r}"
                )

        frame = rows.assign(group=assigned)
        for index, group in enumerate(targets["group"]):
            derived = frame.loc[frame["group"] == group, "cost_daily"].sum()
            max_gap = max(max_gap, abs(float(derived) - float(targets.loc[index, "cost_daily"])))

    mapping_frame = pd.DataFrame(sorted(mapping.items()), columns=["product", "group"]).sort_values(
        ["group", "product"], ignore_index=True
    )
    return mapping_frame, max_gap


def load_cba(costs_path: Path, products_path: Path, area: str) -> CbaBundle:
    costs = read_percapita_costs(costs_path, area)
    products = read_products(products_path, area)
    groups = read_groups(products_path, area)

    cost_periods = set(costs["period"])
    product_periods = set(products["period"])
    group_periods = set(groups["period"])
    if not cost_periods == product_periods == group_periods:
        raise IngestError(
            f"CBA {area}: los periodos de costos, productos y grupos no coinciden "
            f"(costos {min(cost_periods)}–{max(cost_periods)}; "
            f"productos {min(product_periods)}–{max(product_periods)})"
        )

    mapping, gap = assign_product_groups(products, groups, area=area)
    merged = products.merge(mapping, on="product", how="left", validate="many_to_one")
    if merged["group"].isna().any():
        missing = sorted(merged.loc[merged["group"].isna(), "product"].unique())
        raise IngestError(f"CBA {area}: productos sin grupo asignado: {missing}")

    reference = float(groups["kcal_daily"].sum() / groups["period"].nunique())
    if abs(reference - REFERENCE_KCAL[area]) > 0.01:
        raise IngestError(
            f"CBA {area}: se esperaban {REFERENCE_KCAL[area]:.0f} kcal diarias y "
            f"los datos suman {reference:.2f}"
        )

    # Consistencia: costo per cápita publicado contra la suma de productos.
    totals = merged.groupby("period", as_index=False)["cost_daily"].sum()
    check = costs[["period", "daily_cost"]].merge(totals, on="period")
    gap_percapita = float((check["daily_cost"] - check["cost_daily"]).abs().max())
    if gap_percapita > 0.25:
        raise IngestError(
            f"CBA {area}: la suma de productos difiere del costo per cápita en "
            f"Q{gap_percapita:.2f} por día"
        )

    zero_kcal = sorted(merged.loc[merged["zero_kcal"], "product"].unique().tolist())

    return CbaBundle(
        area=area,
        costs=costs,
        products=merged.sort_values(["year", "month"], ignore_index=True),
        groups=groups,
        product_groups=mapping,
        reference_kcal=reference,
        max_group_cost_gap=gap,
        zero_kcal_products=zero_kcal,
    )


def cost_per_1000_kcal(cost: float, kcal: float) -> float | None:
    """Costo de 1 000 kcal; ``None`` cuando el alimento no aporta energía.

    Regla del PRD: la sal y el agua purificada (0 kcal) nunca entran al cálculo
    de costo por 1 000 kcal, ni al numerador ni al denominador.
    """
    if kcal is None or float(kcal) <= _ZERO_KCAL_TOLERANCE:
        return None
    return float(cost) / float(kcal) * 1000.0
