"""Serie del IPC: bases 2023 y 2024, empalme oficial y cálculo directo (inválido).

El IPC de Guatemala cambió de base: diciembre 2023 = 100 para 2024 y base 2024
para 2025-2026. Encadenar los índices publicados de ambas bases sin el empalme
produce variaciones falsas (enero 2025: −0,67 % en vez del +0,50 % oficial).
Aquí se conservan ambos cálculos de forma explícita: ``official_*`` viene del
archivo de empalme del INE y ``direct_*`` del cociente ingenuo entre archivos,
marcado con ``cross_base_*`` cuando mezcla bases.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .errors import IngestError
from .months import month_name, month_number, period, shift_period

BASE_BREAK_PERIOD = "2025-01"
_OUTPUT_FIRST = "2024-01"
_OUTPUT_LAST = "2026-12"


def _normalize(text: object) -> str:
    value = unicodedata.normalize("NFKD", str(text))
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", value.strip().lower())


def _read(path: Path, *, context: str) -> pd.DataFrame:
    try:
        frame = pd.read_excel(path, sheet_name=0, header=0, engine="calamine")
    except Exception as exc:  # noqa: BLE001
        raise IngestError(f"{context}: no fue posible leer {path.name}: {exc}") from exc
    return frame.dropna(how="all")


def _find_column(frame: pd.DataFrame, needle: str, *, context: str) -> str:
    for column in frame.columns:
        if needle in _normalize(column):
            return str(column)
    available = ", ".join(repr(str(c)) for c in frame.columns)
    raise IngestError(f"{context}: falta la columna que contiene {needle!r}: {available}")


def _months(frame: pd.DataFrame, *, context: str) -> pd.DataFrame:
    year_col = next((c for c in frame.columns if _normalize(c) == "ano"), None)
    month_col = next((c for c in frame.columns if _normalize(c) == "mes"), None)
    if year_col is None:
        raise IngestError(f"{context}: falta la columna 'Año'")
    if month_col is None:
        raise IngestError(f"{context}: falta la columna 'Mes'")
    out = frame.copy()
    out["year"] = pd.to_numeric(out[year_col], errors="coerce").astype("Int64")
    out["month"] = [month_number(value) for value in out[month_col]]
    out["month_name"] = [month_name(value) for value in out["month"]]
    out["period"] = [period(y, m) for y, m in zip(out["year"], out["month"], strict=True)]
    return out


@dataclass(slots=True)
class IpcBundle:
    monthly: pd.DataFrame
    link_factor: float
    dec_2024_index_dec2023_base: float
    jan_2025_index_2024_base: float
    official_jan_2025_monthly_var: float
    direct_jan_2025_monthly_var: float

    @property
    def periods(self) -> list[str]:
        return self.monthly["period"].tolist()


def read_general_index_base_2023(path: Path) -> pd.DataFrame:
    """Índice general República 2024, base diciembre 2023 = 100."""
    context = "IPC base dic-2023"
    frame = _months(_read(path, context=context), context=context)
    code_col = _find_column(frame, "codigo", context=context)
    frame = frame[pd.to_numeric(frame[code_col], errors="coerce") == 0]
    rep_col = _find_column(frame, "rep", context=context)
    frame = frame.assign(index_value=pd.to_numeric(frame[rep_col], errors="coerce"))
    frame = frame.dropna(subset=["index_value"])
    frame = frame[frame["year"] == 2024]
    frame = frame.sort_values(["year", "month"], ignore_index=True)
    if len(frame) != 12:
        raise IngestError(f"{context}: se esperaban 12 meses de 2024 y se encontraron {len(frame)}")
    return frame[["year", "month", "month_name", "period", "index_value"]]


def read_general_index_base_2024(path: Path) -> pd.DataFrame:
    """Índice general República 2025-2026, base 2024 = 100."""
    context = "IPC base 2024"
    frame = _months(_read(path, context=context), context=context)
    description = next((c for c in frame.columns if _normalize(c) == "descripcion"), None)
    if description is None:
        raise IngestError(f"{context}: falta la columna 'Descripción'")
    general = frame[frame[description].map(_normalize) == "indice general"]
    rep_col = _find_column(general, "republica", context=context)
    general = general.assign(index_value=pd.to_numeric(general[rep_col], errors="coerce"))
    general = general.dropna(subset=["index_value"])
    general = general.sort_values(["year", "month"], ignore_index=True)
    duplicates = general.duplicated(subset=["year", "month"])
    if duplicates.any():
        raise IngestError(f"{context}: el índice general está duplicado por mes")
    if len(general) < 12:
        raise IngestError(f"{context}: serie demasiado corta ({len(general)} meses)")
    return general[["year", "month", "month_name", "period", "index_value"]]


def read_splice(path: Path) -> pd.DataFrame:
    """Serie empalmada oficial con variaciones mensual, acumulada e interanual."""
    context = "Empalme IPC"
    frame = _months(_read(path, context=context), context=context)
    index_2023 = _find_column(frame, "base diciembre 2023", context=context)
    index_2024 = _find_column(frame, "base 2024", context=context)
    var_monthly = _find_column(frame, "variacion mensual", context=context)
    var_accumulated = _find_column(frame, "variacion acumulada", context=context)
    var_interannual = _find_column(frame, "variacion interanual", context=context)

    out = frame.rename(
        columns={
            index_2023: "official_index_dec2023",
            index_2024: "official_index_2024",
            var_monthly: "official_monthly_var",
            var_accumulated: "official_accum_var",
            var_interannual: "official_interannual_var",
        }
    )
    for column in (
        "official_index_dec2023",
        "official_index_2024",
        "official_monthly_var",
        "official_accum_var",
        "official_interannual_var",
    ):
        out[column] = pd.to_numeric(out[column], errors="coerce")

    out = out.sort_values(["year", "month"], ignore_index=True)
    if out.duplicated(subset=["year", "month"]).any():
        raise IngestError(f"{context}: hay meses duplicados en la serie empalmada")
    return out[
        [
            "year",
            "month",
            "month_name",
            "period",
            "official_index_dec2023",
            "official_index_2024",
            "official_monthly_var",
            "official_accum_var",
            "official_interannual_var",
        ]
    ]


def _direct_monthly_var(
    period_label: str,
    raw_2023: dict[str, float],
    raw_2024: dict[str, float],
) -> tuple[float | None, bool]:
    """Variación mes a mes usando los índices publicados, sin empalme."""
    year, month = int(period_label[:4]), int(period_label[5:])
    if year == 2024 and month == 1:
        # Base diciembre 2023 = 100 por definición.
        return (raw_2023[period_label] / 100.0 - 1.0) * 100.0, False
    if year == 2024:
        previous = shift_period(period_label, -1)
        return (raw_2023[period_label] / raw_2023[previous] - 1.0) * 100.0, False
    if period_label == BASE_BREAK_PERIOD:
        # Trampa: diciembre 2024 viene de la base 2023 y enero 2025 de la base 2024.
        return (raw_2024[period_label] / raw_2023["2024-12"] - 1.0) * 100.0, True
    previous = shift_period(period_label, -1)
    return (raw_2024[period_label] / raw_2024[previous] - 1.0) * 100.0, False


def _direct_interannual_var(
    period_label: str,
    raw_2023: dict[str, float],
    raw_2024: dict[str, float],
    official_index_dec2023: dict[str, float],
) -> tuple[float | None, bool]:
    """Variación 12 meses usando los índices publicados, sin empalme."""
    year, month = int(period_label[:4]), int(period_label[5:])
    previous = f"{year - 1:04d}-{month:02d}"
    if year == 2024:
        # Misma base (dic-2023): el cálculo directo coincide con el oficial.
        if previous not in official_index_dec2023:
            return None, False
        return (
            official_index_dec2023[period_label] / official_index_dec2023[previous] - 1.0
        ) * 100.0, False
    if year == 2025:
        # Trampa: 2025 está en base 2024 y 2024 en base dic-2023.
        return (raw_2024[period_label] / raw_2023[previous] - 1.0) * 100.0, True
    return (raw_2024[period_label] / raw_2024[previous] - 1.0) * 100.0, False


def build_ipc_monthly(
    base_2023: pd.DataFrame,
    base_2024: pd.DataFrame,
    splice: pd.DataFrame,
) -> IpcBundle:
    link_frame = splice[splice["period"] == "2024-12"]
    if link_frame.empty:
        raise IngestError("Empalme IPC: falta diciembre 2024 para calcular el factor de enlace")
    official_2024_dec = float(link_frame.iloc[0]["official_index_2024"])
    official_2023_dec = float(link_frame.iloc[0]["official_index_dec2023"])
    link_factor = official_2024_dec / official_2023_dec

    jan_2025 = splice[splice["period"] == BASE_BREAK_PERIOD]
    if jan_2025.empty:
        raise IngestError("Empalme IPC: falta enero 2025")

    raw_2023 = dict(zip(base_2023["period"], base_2023["index_value"].astype(float), strict=True))
    raw_2024 = dict(zip(base_2024["period"], base_2024["index_value"].astype(float), strict=True))
    official_index_dec2023 = dict(
        zip(
            splice["period"],
            splice["official_index_dec2023"].astype(float),
            strict=True,
        )
    )

    output = splice[(splice["period"] >= _OUTPUT_FIRST) & (splice["period"] <= _OUTPUT_LAST)].copy()
    output = output[output["period"].isin(set(raw_2023) | set(raw_2024))]
    output = output.sort_values(["year", "month"], ignore_index=True)

    rows = []
    for row in output.itertuples(index=False):
        label = row.period
        direct_monthly, cross_monthly = _direct_monthly_var(label, raw_2023, raw_2024)
        direct_interannual, cross_interannual = _direct_interannual_var(
            label, raw_2023, raw_2024, official_index_dec2023
        )
        raw_index = raw_2023.get(label, raw_2024.get(label))
        rows.append(
            {
                "period": label,
                "year": int(row.year),
                "month": int(row.month),
                "month_name": row.month_name,
                "published_index": raw_index,
                "published_base": "dic-2023" if int(row.year) == 2024 else "2024",
                "official_index_dec2023": float(row.official_index_dec2023),
                "official_index_2024": float(row.official_index_2024),
                "official_monthly_var": float(row.official_monthly_var),
                "official_accum_var": float(row.official_accum_var),
                "official_interannual_var": float(row.official_interannual_var),
                "direct_monthly_var": direct_monthly,
                "direct_interannual_var": direct_interannual,
                "cross_base_monthly": cross_monthly,
                "cross_base_interannual": cross_interannual,
                "direct_monthly_gap_pp": None
                if direct_monthly is None
                else direct_monthly - float(row.official_monthly_var),
                "direct_interannual_gap_pp": None
                if direct_interannual is None
                else direct_interannual - float(row.official_interannual_var),
            }
        )

    monthly = pd.DataFrame(rows)
    jan_row = monthly[monthly["period"] == BASE_BREAK_PERIOD]
    if jan_row.empty:
        raise IngestError("IPC: enero 2025 quedó fuera de la tabla mensual")
    official_jan = float(jan_row.iloc[0]["official_monthly_var"])
    direct_jan = float(jan_row.iloc[0]["direct_monthly_var"])

    # Verificación dura del dato publicado: +0,50 % mensual en enero 2025.
    if abs(official_jan - 0.50) > 0.01:
        raise IngestError(
            f"IPC: se esperaba +0,50 % en enero 2025 y el empalme dice {official_jan:.4f} %"
        )
    if abs(direct_jan - (-0.67)) > 0.05:
        raise IngestError(
            "IPC: el cálculo directo de enero 2025 no reproduce la distorsión "
            f"documentada (-0,67 %); se obtuvo {direct_jan:.4f} %"
        )

    return IpcBundle(
        monthly=monthly,
        link_factor=link_factor,
        dec_2024_index_dec2023_base=official_2023_dec,
        jan_2025_index_2024_base=float(jan_2025.iloc[0]["official_index_2024"]),
        official_jan_2025_monthly_var=official_jan,
        direct_jan_2025_monthly_var=direct_jan,
    )
