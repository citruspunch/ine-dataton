"""CBAU / CBAR food-basket ingestion.

Two record families are produced:

* per-capita monthly cost (one row per month), and
* product / food-group rows from the historical workbooks.

The product row's ``value`` is the implicit price for the base quantity (for
example ``Q 7.95 / 454 g``), not the product's contribution to the daily basket.
That contribution is kept in ``extra.monthlyCost`` for context.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .config import SourceSpec
from .model import Record
from .parsing import clean_text, month_start, normalize_text, parse_month_es, parse_number


def _columns(frame: pd.DataFrame) -> dict[str, str]:
    return {normalize_text(column): column for column in frame.columns}


def _pick(columns: dict[str, str], *candidates: str) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return columns[candidate]
    return None


def _pick_prefix(columns: dict[str, str], prefix: str) -> str | None:
    for normalized, original in columns.items():
        if normalized.startswith(prefix):
            return original
    return None


def _region_from(spec: SourceSpec) -> str:
    return "Rural" if spec.id.startswith("cbar") else "Urbana"


def _basket_name(region: str) -> str:
    return f"Canasta Básica Alimentaria {region}"


def _percapita_records(spec: SourceSpec, path: Path) -> list[Record]:
    region = _region_from(spec)
    frame = pd.read_excel(path, dtype=object)
    columns = _columns(frame)
    year_col = _pick(columns, "ano")
    month_col = _pick(columns, "mes")
    daily_col = _pick_prefix(columns, "costo diario")
    monthly_col = _pick_prefix(columns, "costo mensual")
    if not all([year_col, month_col, daily_col, monthly_col]):
        raise ValueError(f"{spec.filename}: faltan columnas de año, mes o costo")

    records: list[Record] = []
    for row in frame.to_dict(orient="records"):
        record_date = month_start(row.get(year_col), parse_month_es(row.get(month_col)))
        if record_date is None:
            continue
        monthly, _ = parse_number(row.get(monthly_col))
        daily, _ = parse_number(row.get(daily_col))
        flags = ["missing_value"] if monthly is None else []
        records.append(
            Record(
                id=f"{spec.id}-{record_date.year}{record_date.month:02d}",
                source="CBAU" if region == "Urbana" else "CBAR",
                source_group="BASKETS",
                dataset=spec.id,
                item="Costo mensual per cápita",
                category=_basket_name(region),
                metric="Costo mensual per cápita",
                value_kind="cost",
                value=monthly,
                unit="Q por persona al mes",
                metric_unit="Q por persona al mes",
                currency="GTQ",
                date=record_date.isoformat(),
                date_raw=f"{record_date.year}-{record_date.month:02d}",
                date_status="valid",
                year=record_date.year,
                month=record_date.month,
                region=region,
                level="Per cápita",
                status=spec.status,
                flags=flags,
                extra={"dailyCost": daily},
            )
        )
    return records


def _history_records(spec: SourceSpec, path: Path, region: str) -> list[Record]:
    records: list[Record] = []
    workbook = pd.ExcelFile(path)
    for sheet_name in workbook.sheet_names:
        is_group = "grupo" in normalize_text(sheet_name)
        frame = pd.read_excel(path, sheet_name=sheet_name, dtype=object)
        columns = _columns(frame)
        year_col = _pick(columns, "ano")
        month_col = _pick(columns, "mes")
        group_col = _pick(columns, "grupo alimenticio")
        product_col = _pick(columns, "producto")
        quantity_col = _pick(columns, "cantidad base")
        base_unit_col = _pick(columns, "unidad de medida base")
        daily_col = _pick(columns, "costo diario")
        monthly_col = _pick(columns, "costo mensual")
        price_col = _pick(columns, "precio segun unidad de medida base")

        if not all([year_col, month_col, monthly_col]):
            continue

        for index, row in enumerate(frame.to_dict(orient="records")):
            record_date = month_start(row.get(year_col), parse_month_es(row.get(month_col)))
            if record_date is None:
                continue
            monthly, _ = parse_number(row.get(monthly_col))
            daily, _ = parse_number(row.get(daily_col))

            if is_group:
                item = clean_text(row.get(group_col)) if group_col else None
                if not item:
                    continue
                metric = "Costo mensual del grupo"
                value = monthly
                unit = "Q por persona al mes"
                value_kind = "cost"
                level = "Grupo alimenticio"
                flags = ["missing_value"] if value is None else []
                extra: dict[str, Any] = {"dailyCost": daily}
            else:
                item = clean_text(row.get(product_col)) if product_col else None
                if not item:
                    continue
                value, _ = parse_number(row.get(price_col))
                quantity, _ = parse_number(row.get(quantity_col))
                base_unit = clean_text(row.get(base_unit_col)) if base_unit_col else None
                metric = "Precio por unidad base"
                unit = (
                    f"Q por {quantity:g} {base_unit}"
                    if quantity and base_unit
                    else "Q por unidad base"
                )
                value_kind = "price"
                level = "Producto"
                flags = ["missing_value"] if value is None else []
                extra = {
                    "dailyCost": daily,
                    "monthlyCost": monthly,
                    "baseQuantity": quantity,
                    "baseUnit": base_unit,
                }

            records.append(
                Record(
                    id=f"{spec.id}-{index:04d}-{record_date.year}{record_date.month:02d}",
                    source="CBAU" if region == "Urbana" else "CBAR",
                    source_group="BASKETS",
                    dataset=spec.id,
                    item=item,
                    category=_basket_name(region),
                    metric=metric,
                    value_kind=value_kind,
                    value=value,
                    unit=unit,
                    metric_unit=unit,
                    currency="GTQ",
                    date=record_date.isoformat(),
                    date_raw=f"{record_date.year}-{record_date.month:02d}",
                    date_status="valid",
                    year=record_date.year,
                    month=record_date.month,
                    region=region,
                    level=level,
                    status=spec.status,
                    flags=flags,
                    extra=extra,
                )
            )
    return records


def load_baskets(specs: list[SourceSpec], raw_dir: Path) -> list[Record]:
    records: list[Record] = []
    for spec in specs:
        path = raw_dir / spec.filename
        if not path.exists():
            raise FileNotFoundError(f"No existe {path}; ejecute primero la adquisición de datos.")
        if "percapita" in spec.id:
            records.extend(_percapita_records(spec, path))
        else:
            records.extend(_history_records(spec, path, _region_from(spec)))
    return records
