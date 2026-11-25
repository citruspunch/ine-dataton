"""IPMC historical index ingestion (89 materials, base December 2018 = 100)."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pandas as pd

from .config import SourceSpec
from .model import Record
from .parsing import clean_text, parse_month_es, parse_number

_YEAR_HEADER = re.compile(r"(20\d{2})")
_GROUP_HEADER = re.compile(r"^([A-Z])\.\s*(.+)$")


def _month_columns(frame: pd.DataFrame) -> list[tuple[int, int, int]]:
    """Return ``(column, year, month)`` for every dated value column."""

    years: dict[int, int] = {}
    current_year: int | None = None
    for col in range(frame.shape[1]):
        cell = frame.iat[0, col]
        text = clean_text(cell)
        if text and "ÍNDICE" in text.upper():
            match = _YEAR_HEADER.search(text)
            if match:
                current_year = int(match.group(1))
        if current_year is not None:
            years[col] = current_year

    columns: list[tuple[int, int, int]] = []
    for col in range(4, frame.shape[1]):
        year = years.get(col)
        month = parse_month_es(frame.iat[1, col])
        if year and month:
            columns.append((col, year, month))
    return columns


def _clean_item_name(value: str) -> str:
    # Drop the product number inside a group ("1. Angular…") but keep
    # subsection codes such as "1.1 Varilla…".
    return re.sub(r"^\d+\.\s+(?=\D)", "", value).strip()


def load_ipmc(spec: SourceSpec, raw_dir: Path) -> list[Record]:
    path = raw_dir / spec.filename
    if not path.exists():
        raise FileNotFoundError(f"No existe {path}; ejecute primero la adquisición de datos.")

    frame = pd.read_excel(path, header=None)
    month_columns = _month_columns(frame)
    if not month_columns:
        raise ValueError(f"{spec.filename}: no se encontraron columnas mensuales")

    records: list[Record] = []
    group_name = "Sin grupo"
    subgroup_name: str | None = None

    for row_index in range(2, frame.shape[0]):
        number_raw = frame.iat[row_index, 0]
        label = clean_text(frame.iat[row_index, 1])
        if label is None:
            continue

        try:
            material_no = int(float(number_raw))
        except (TypeError, ValueError):
            material_no = None

        if material_no is None:
            if label.upper().startswith("MATERIAL"):
                continue
            match = _GROUP_HEADER.match(label)
            if match:
                group_name = match.group(2).strip()
                subgroup_name = None
                continue
            if label.upper().startswith("T."):
                group_name = label[2:].strip()
                subgroup_name = None
                continue
            # A subsection such as "1. HIERRO GRADO 40".
            if re.match(r"^\d+\.\s", label):
                subgroup_name = label
            continue

        name = _clean_item_name(label)
        material_unit = clean_text(frame.iat[row_index, 2]) or "No especificada"
        base_value, _ = parse_number(frame.iat[row_index, 3])

        for col, year, month in month_columns:
            value, _ = parse_number(frame.iat[row_index, col])
            if value is None:
                continue
            record_date = date(year, month, 1)
            records.append(
                Record(
                    id=f"{spec.id}-{material_no:03d}-{year}{month:02d}",
                    source="IPMC",
                    source_group="IPMC",
                    dataset=spec.id,
                    item=name,
                    category=group_name,
                    metric="Índice IPMC",
                    value_kind="index",
                    value=value,
                    unit=material_unit,
                    metric_unit="Índice (base dic-2018 = 100)",
                    currency=None,
                    date=record_date.isoformat(),
                    date_raw=f"{year}-{month:02d}",
                    date_status="valid",
                    year=year,
                    month=month,
                    region="Región I Metropolitana",
                    level="Material",
                    context=subgroup_name,
                    status=spec.status,
                    extra={"materialNo": material_no, "baseValue": base_value},
                )
            )

    return records
