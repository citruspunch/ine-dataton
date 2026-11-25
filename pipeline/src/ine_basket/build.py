"""Construcción de las tablas limpias y del paquete de datos que consume Next.js."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from . import __version__
from .cba import (
    DAYS_PER_MONTH,
    CbaBundle,
    load_cba,
)
from .download import DatasetFile, ensure_datasets
from .errors import IngestError
from .ipc import (
    BASE_BREAK_PERIOD,
    IpcBundle,
    build_ipc_monthly,
    read_general_index_base_2023,
    read_general_index_base_2024,
    read_splice,
)
from .months import month_name
from .registry import DATASETS
from .simulator import basket_cost_per_1000_kcal


@dataclass(slots=True)
class PipelineResult:
    tables: dict[str, pd.DataFrame]
    manifest: dict[str, Any]
    web_payload: dict[str, Any]
    cba: dict[str, CbaBundle]
    ipc: IpcBundle


def _round(value: Any, digits: int) -> float | None:
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return round(number, digits)


def _derived_groups(products: pd.DataFrame) -> pd.DataFrame:
    """Agrupa los productos por grupo alimenticio y periodo.

    La suma de los productos reproduce el total per cápita; la hoja de grupos del
    INE se conserva al lado (``official_*``) para auditar diferencias de redondeo.
    ``caloric_cost`` deja fuera sal y agua para el costo por 1 000 kcal.
    """
    working = products.assign(
        caloric_cost_daily=[
            cost if not zero else 0.0
            for cost, zero in zip(products["cost_daily"], products["zero_kcal"], strict=True)
        ],
        caloric_kcal_daily=[
            kcal if not zero else 0.0
            for kcal, zero in zip(products["kcal_daily"], products["zero_kcal"], strict=True)
        ],
    )
    grouped = (
        working.groupby(["area", "year", "month", "month_name", "period", "group"], as_index=False)
        .agg(
            kcal_daily=("kcal_daily", "sum"),
            grams_daily=("grams_daily", "sum"),
            cost_daily=("cost_daily", "sum"),
            caloric_cost_daily=("caloric_cost_daily", "sum"),
            caloric_kcal_daily=("caloric_kcal_daily", "sum"),
        )
        .rename(columns={"group": "group_name"})
    )
    grouped["cost_monthly"] = grouped["cost_daily"] * DAYS_PER_MONTH
    grouped["kcal_monthly"] = grouped["kcal_daily"] * DAYS_PER_MONTH
    grouped["cost_per_1000_kcal"] = [
        basket_cost_per_1000_kcal([(cost, kcal)])
        for cost, kcal in zip(
            grouped["caloric_cost_daily"], grouped["caloric_kcal_daily"], strict=True
        )
    ]
    return grouped


def _attach_official_groups(derived: pd.DataFrame, official: pd.DataFrame) -> pd.DataFrame:
    reference = official.rename(
        columns={
            "group": "group_name",
            "cost_daily": "official_cost_daily",
            "kcal_daily": "official_kcal_daily",
            "grams_daily": "official_grams_daily",
            "cost_monthly": "official_cost_monthly",
        }
    )[
        [
            "area",
            "period",
            "group_name",
            "official_cost_daily",
            "official_kcal_daily",
            "official_grams_daily",
            "official_cost_monthly",
        ]
    ]
    merged = derived.merge(
        reference,
        on=["area", "period", "group_name"],
        how="left",
        validate="one_to_one",
    )
    if merged["official_cost_daily"].isna().any():
        missing = merged.loc[merged["official_cost_daily"].isna(), "group_name"].unique()
        raise IngestError(f"Grupos sin contraparte oficial: {missing.tolist()}")
    merged["cost_gap_vs_official"] = merged["cost_daily"] - merged["official_cost_daily"]
    merged["cost_gap_pct"] = merged["cost_gap_vs_official"] / merged["official_cost_daily"] * 100
    return merged


def _monthly_table(cba: dict[str, CbaBundle]) -> pd.DataFrame:
    frames = []
    for _area, bundle in cba.items():
        rows = []
        for label, chunk in bundle.products.groupby("period", sort=True):
            zero = chunk["zero_kcal"].to_numpy()
            costs = chunk["cost_daily"].to_numpy(dtype=float)
            kcals = chunk["kcal_daily"].to_numpy(dtype=float)
            rows.append(
                {
                    "period": label,
                    "total_kcal": float(kcals.sum()),
                    "total_cost": float(costs.sum()),
                    "caloric_cost_daily": float(costs[~zero].sum()),
                    "excluded_cost_daily": float(costs[zero].sum()),
                    "cost_per_1000_kcal": basket_cost_per_1000_kcal(zip(costs, kcals, strict=True)),
                }
            )
        totals = pd.DataFrame(rows)
        frame = bundle.costs.merge(totals, on="period", how="left", validate="one_to_one")
        frame["daily_kcal"] = frame["total_kcal"]
        frame["coverage_pct"] = frame["daily_kcal"] / bundle.reference_kcal * 100
        frame["cost_gap_vs_products"] = frame["daily_cost"] - frame["total_cost"]
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def _products_table(cba: dict[str, CbaBundle]) -> pd.DataFrame:
    frames = []
    for area, bundle in cba.items():
        frame = bundle.products.copy()
        frame["area"] = area
        frames.append(frame)
    result = pd.concat(frames, ignore_index=True)
    result["unit_label"] = result.apply(
        lambda row: f"{row['base_quantity']:,.0f} {row['base_unit'].lower()}",
        axis=1,
    )
    return result


def _json_number(value: Any, digits: int) -> float | None:
    return _round(value, digits)


def _area_payload(bundle: CbaBundle, groups: pd.DataFrame, monthly: pd.DataFrame) -> dict[str, Any]:
    months: list[dict[str, Any]] = []
    costs = monthly.set_index("period")
    products_by_period = {
        label: chunk.set_index("product")
        for label, chunk in bundle.products.groupby("period", sort=False)
    }
    groups_by_period = {
        label: chunk.set_index("group_name")
        for label, chunk in groups.groupby("period", sort=False)
    }

    # Catálogo estable en el orden de la canasta del INE (primer periodo).
    catalog_source = bundle.products[bundle.products["period"] == bundle.periods[0]]
    catalog = [
        {
            "name": row.product,
            "group": row.group,
            "baseQuantity": _json_number(row.base_quantity, 0),
            "baseUnit": row.base_unit,
            "zeroKcal": bool(row.zero_kcal),
        }
        for row in catalog_source.itertuples(index=False)
    ]
    product_order = [item["name"] for item in catalog]
    group_order = [
        str(name) for name in bundle.groups[bundle.groups["period"] == bundle.periods[0]]["group"]
    ]

    for label in bundle.periods:
        cost_row = costs.loc[label]
        product_rows = products_by_period[label]
        group_rows = groups_by_period[label]
        if set(product_order) != set(product_rows.index):
            missing = sorted(set(product_order) ^ set(product_rows.index))
            raise IngestError(f"CBA {bundle.area}: productos distintos en {label}: {missing}")

        product_values = [
            [
                _json_number(product_rows.at[name, "unit_price"], 4),
                _json_number(product_rows.at[name, "kcal_daily"], 3),
                _json_number(product_rows.at[name, "cost_daily"], 4),
                _json_number(product_rows.at[name, "cost_per_1000_kcal"], 2),
            ]
            for name in product_order
        ]
        total_group_cost = float(group_rows["cost_daily"].sum())
        group_values = [
            [
                _json_number(group_rows.at[name, "cost_daily"], 4),
                _json_number(group_rows.at[name, "kcal_daily"], 3),
                _json_number(group_rows.at[name, "cost_per_1000_kcal"], 2),
                _json_number(
                    (group_rows.at[name, "cost_daily"] / total_group_cost * 100)
                    if total_group_cost
                    else None,
                    2,
                ),
            ]
            for name in group_order
        ]

        months.append(
            {
                "period": label,
                "year": int(cost_row["year"]),
                "month": int(cost_row["month"]),
                "monthName": cost_row["month_name"],
                "label": f"{cost_row['month_name']} {int(cost_row['year'])}",
                "dailyCostPerPerson": _json_number(cost_row["daily_cost"], 4),
                "monthlyCostPerPerson": _json_number(cost_row["monthly_cost"], 2),
                "caloricCostPerPersonDay": _json_number(cost_row["caloric_cost_daily"], 4),
                "excludedCostPerPersonDay": _json_number(cost_row["excluded_cost_daily"], 4),
                "dailyKcalPerPerson": _json_number(cost_row["daily_kcal"], 3),
                "coveragePct": _json_number(cost_row["coverage_pct"], 2),
                "costPerThousandKcal": _json_number(cost_row["cost_per_1000_kcal"], 2),
                "productValues": product_values,
                "groupValues": group_values,
            }
        )

    first, last = bundle.periods[0], bundle.periods[-1]
    return {
        "summary": {
            "area": bundle.area,
            "referenceKcal": _json_number(bundle.reference_kcal, 0),
            "productCount": int(bundle.products["product"].nunique()),
            "groupCount": int(bundle.groups["group"].nunique()),
            "zeroKcalProducts": bundle.zero_kcal_products,
            "period": {"first": first, "last": last, "count": len(bundle.periods)},
        },
        "products": catalog,
        "groups": group_order,
        "months": months,
    }


def _ipc_payload(ipc: IpcBundle) -> list[dict[str, Any]]:
    rows = []
    for row in ipc.monthly.itertuples(index=False):
        rows.append(
            {
                "period": row.period,
                "year": int(row.year),
                "month": int(row.month),
                "monthName": row.month_name,
                "officialMonthly": _json_number(row.official_monthly_var, 4),
                "officialInterannual": _json_number(row.official_interannual_var, 4),
                "officialAccumulated": _json_number(row.official_accum_var, 4),
                "directMonthly": _json_number(row.direct_monthly_var, 4),
                "directInterannual": _json_number(row.direct_interannual_var, 4),
                "crossBaseMonthly": bool(row.cross_base_monthly),
                "crossBaseInterannual": bool(row.cross_base_interannual),
                "directMonthlyGapPp": _json_number(row.direct_monthly_gap_pp, 4),
                "directInterannualGapPp": _json_number(row.direct_interannual_gap_pp, 4),
                "publishedIndex": _json_number(row.published_index, 6),
                "publishedBase": row.published_base,
                "officialIndexDec2023": _json_number(row.official_index_dec2023, 6),
                "officialIndex2024": _json_number(row.official_index_2024, 6),
            }
        )
    return rows


def _checks(cba: dict[str, CbaBundle], products: pd.DataFrame) -> dict[str, Any]:
    per_area = {}
    for area, bundle in cba.items():
        subset = products[products["area"] == area]
        coverage = subset.groupby("period")["kcal_daily"].sum()
        per_area[area] = {
            "periods": len(bundle.periods),
            "products": int(subset["product"].nunique()),
            "groups": int(bundle.groups["group"].nunique()),
            "kcalPerDay": _json_number(float(coverage.mean()), 3),
            "maxGroupCostGapQ": _json_number(bundle.max_group_cost_gap, 4),
            "zeroKcalProducts": bundle.zero_kcal_products,
        }
    return per_area


def build_tables(
    files: dict[str, DatasetFile],
) -> tuple[dict[str, pd.DataFrame], IpcBundle, dict[str, CbaBundle]]:
    """Lee los siete archivos y devuelve tablas limpias y consistentes."""
    cba: dict[str, CbaBundle] = {}
    for area, cost_key, products_key in (
        ("Urbana", "cba_urbana_percapita", "cba_urbana_productos"),
        ("Rural", "cba_rural_percapita", "cba_rural_productos"),
    ):
        cba[area] = load_cba(
            files[cost_key].path,
            files[products_key].path,
            area,
        )

    base_2023 = read_general_index_base_2023(files["ipc_2024"].path)
    base_2024 = read_general_index_base_2024(files["ipc_2025"].path)
    splice = read_splice(files["ipc_empalme"].path)
    ipc = build_ipc_monthly(base_2023, base_2024, splice)

    periods = set(ipc.periods)
    for area, bundle in cba.items():
        if set(bundle.periods) != periods:
            raise IngestError(
                f"Los periodos de la CBA {area} no coinciden con los del IPC. "
                f"CBA: {min(bundle.periods)}–{max(bundle.periods)}; "
                f"IPC: {min(periods)}–{max(periods)}"
            )

    monthly = _monthly_table(cba)
    products = _products_table(cba)

    derived = _derived_groups(products)
    official_groups = pd.concat([bundle.groups for bundle in cba.values()], ignore_index=True)
    groups = _attach_official_groups(derived, official_groups)

    # Orden cronológico explícito: nunca por etiqueta alfabética.
    tables = {
        "cba_monthly": monthly.sort_values(["area", "year", "month"], ignore_index=True),
        "cba_products": products.sort_values(["area", "year", "month"], ignore_index=True),
        "cba_groups": groups.sort_values(["area", "year", "month"], ignore_index=True),
        "ipc_monthly": ipc.monthly,
    }
    return tables, ipc, cba


def build_pipeline(
    *,
    repo_root: Path,
    raw_dir: Path,
    refresh: bool = False,
    offline: bool = False,
    downloader=None,
    clock=None,
) -> PipelineResult:
    """Orquesta descarga/caché, lectura, validación y payload para la web."""
    from .download import utc_now_iso

    resolved_clock = clock or utc_now_iso
    generated_at = resolved_clock()

    files_list = ensure_datasets(
        DATASETS,
        raw_dir,
        raw_dir / "download-registry.json",
        refresh=refresh,
        offline=offline,
        downloader=downloader,
        clock=resolved_clock,
    )
    files = {entry.spec.key: entry for entry in files_list}

    tables, ipc, cba = build_tables(files)
    checks = _checks(cba, tables["cba_products"])

    area_payloads = {
        area: _area_payload(
            bundle,
            tables["cba_groups"][tables["cba_groups"]["area"] == area],
            tables["cba_monthly"][tables["cba_monthly"]["area"] == area],
        )
        for area, bundle in cba.items()
    }
    first = min(bundle.periods[0] for bundle in cba.values())
    last = max(bundle.periods[-1] for bundle in cba.values())
    periods = [row["period"] for row in area_payloads["Urbana"]["months"]]

    web_payload = {
        "meta": {
            "generatedAtUtc": generated_at,
            "generator": f"ine-basket {__version__}",
            "period": {
                "first": first,
                "last": last,
                "count": len(periods),
                "firstLabel": f"{month_name(int(first[5:]))} {first[:4]}",
                "lastLabel": f"{month_name(int(last[5:]))} {last[:4]}",
            },
            "daysPerMonth": DAYS_PER_MONTH,
            "areas": {area: payload["summary"] for area, payload in area_payloads.items()},
            "checks": checks,
            "splice": {
                "baseBreakPeriod": BASE_BREAK_PERIOD,
                "linkFactor2023To2024": _json_number(ipc.link_factor, 6),
                "dec2024IndexDec2023Base": _json_number(ipc.dec_2024_index_dec2023_base, 6),
                "jan2025Index2024Base": _json_number(ipc.jan_2025_index_2024_base, 6),
                "officialJan2025Monthly": _json_number(ipc.official_jan_2025_monthly_var, 4),
                "directJan2025Monthly": _json_number(ipc.direct_jan_2025_monthly_var, 4),
            },
            "sources": [entry.manifest_entry(repo_root) for entry in files_list],
        },
        "areas": {
            area: {
                "products": payload["products"],
                "groups": payload["groups"],
                "months": payload["months"],
            }
            for area, payload in area_payloads.items()
        },
        "ipc": _ipc_payload(ipc),
    }

    manifest = {
        "schema_version": 1,
        "generated_at_utc": generated_at,
        "generator": f"ine-basket {__version__}",
        "periods": {
            "first": first,
            "last": last,
            "count": len(periods),
            "list": periods,
        },
        "sources": [entry.manifest_entry(repo_root) for entry in files_list],
        "rules": {
            "days_per_month": DAYS_PER_MONTH,
            "month_ordering": "cronológica por (año, número de mes)",
            "zero_kcal_excluded_from_cost_per_1000_kcal": True,
            "cpi_variation_source": "ipc_emprepu_es25.xlsx (empalme oficial INE)",
            "base_break_period": BASE_BREAK_PERIOD,
            "link_factor_2023_to_2024": _json_number(ipc.link_factor, 9),
            "official_jan_2025_monthly_var_pct": _json_number(ipc.official_jan_2025_monthly_var, 9),
            "direct_jan_2025_monthly_var_pct": _json_number(ipc.direct_jan_2025_monthly_var, 9),
        },
        "checks": checks,
    }
    return PipelineResult(
        tables=tables,
        manifest=manifest,
        web_payload=web_payload,
        cba=cba,
        ipc=ipc,
    )
