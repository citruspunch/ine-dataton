"""DPIR (Precios de Referencia) ingestion.

Both frozen snapshots are loaded.  The 2023 workbook is the newer, preferred
source: when the same observation appears in both files, the 2022 copy is
marked as a duplicate and excluded from numeric summaries.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .config import SourceSpec
from .model import Record
from .parsing import clean_text, is_empty, normalize_text, parse_date, parse_number


def _pick(columns: dict[str, str], *candidates: str) -> str | None:
    for candidate in candidates:
        if candidate in columns:
            return columns[candidate]
    return None


def _column_lookup(df: pd.DataFrame) -> dict[str, str]:
    return {normalize_text(column): column for column in df.columns}


def _records_from_frame(df: pd.DataFrame, spec: SourceSpec) -> list[Record]:
    columns = _column_lookup(df)
    nog_col = _pick(columns, "nog", "no g")
    product_col = _pick(columns, "producto")
    category_col = _pick(columns, "categoria")
    unit_col = _pick(columns, "presentacion")
    price_col = _pick(columns, "precio de referencia q", "precio de referencia")
    date_col = _pick(columns, "fecha de entrega")
    description_col = _pick(columns, "caracteristicas")

    missing = [
        name
        for name, value in {
            "Producto": product_col,
            "Precio de Referencia (Q)": price_col,
            "Fecha de Entrega": date_col,
        }.items()
        if value is None
    ]
    if missing:
        raise ValueError(f"{spec.filename}: faltan columnas obligatorias {missing}")

    records: list[Record] = []
    for index, row in enumerate(df.to_dict(orient="records")):
        raw_nog = clean_text(row.get(nog_col)) if nog_col else None
        # "Sin Dato" is a placeholder, not a real operation number.
        nog = None if is_empty(raw_nog) else raw_nog
        item = clean_text(row.get(product_col))
        category = clean_text(row.get(category_col)) if category_col else None
        unit = clean_text(row.get(unit_col)) if unit_col else None
        description = clean_text(row.get(description_col)) if description_col else None
        price_value, had_comma = parse_number(row.get(price_col))
        parsed_date = parse_date(row.get(date_col))

        flags: list[str] = []
        if had_comma:
            flags.append("thousands_comma")
        if parsed_date.status == "invalid":
            flags.append("invalid_date")
        elif parsed_date.status == "missing":
            flags.append("missing_date")
        if not nog:
            flags.append("missing_nog")
        if price_value is None:
            flags.append("missing_value")
        if not item:
            flags.append("missing_product")

        record = Record(
            id=f"{spec.id}-{index:06d}",
            source="DPIR",
            source_group="DPIR",
            dataset=spec.id,
            item=item or "Sin producto",
            category=category or "Sin categoría",
            metric="Precio de referencia",
            value_kind="price",
            value=price_value,
            unit=unit or "Sin presentación",
            metric_unit="Q",
            currency="GTQ",
            date=parsed_date.iso,
            date_raw=parsed_date.raw,
            date_status=parsed_date.status,
            year=parsed_date.value.year if parsed_date.value else None,
            month=parsed_date.value.month if parsed_date.value else None,
            nog=nog,
            description=description,
            status=spec.status,
            flags=flags,
        )
        records.append(record)
    return records


def load_dpir(specs: list[SourceSpec], raw_dir: Path) -> list[Record]:
    records: list[Record] = []
    for spec in specs:
        path = raw_dir / spec.filename
        if not path.exists():
            raise FileNotFoundError(f"No existe {path}; ejecute primero la adquisición de datos.")
        if spec.kind == "csv":
            frame = pd.read_csv(
                path,
                dtype=str,
                encoding="utf-8-sig",
                keep_default_na=False,
            )
        else:
            frame = pd.read_excel(path, dtype=str)
        records.extend(_records_from_frame(frame, spec))
    return records


def dictionary_entries(path: Path) -> list[dict[str, Any]]:
    """Read the DPIR variable dictionary for the traceability panel."""

    if not path.exists():
        return []
    try:
        frame = pd.read_excel(path, sheet_name="Diccionario de variables", dtype=str)
    except (ValueError, OSError):
        return []
    columns = {normalize_text(column): column for column in frame.columns}
    variable_col = columns.get("variable")
    description_col = columns.get("descripcion")
    if not variable_col:
        return []

    entries: list[dict[str, Any]] = []
    for row in frame.to_dict(orient="records"):
        variable = clean_text(row.get(variable_col))
        description = clean_text(row.get(description_col)) if description_col else None
        if variable:
            entries.append({"variable": variable, "description": description or ""})
    return entries
