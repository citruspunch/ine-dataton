"""ICC (Índice de Costos de Construcción) ingestion, 2026 VSB workbook."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pandas as pd

from .config import SourceSpec
from .model import Record
from .parsing import clean_text, parse_month_es, parse_number

_YEAR = re.compile(r"(20\d{2})")


def _month_columns(frame: pd.DataFrame) -> list[tuple[int, int, int]]:
    years: dict[int, int] = {}
    current_year: int | None = None
    for col in range(frame.shape[1]):
        text = clean_text(frame.iat[0, col])
        if text and "AÑO" in text.upper():
            match = _YEAR.search(text)
            if match:
                current_year = int(match.group(1))
        if current_year:
            years[col] = current_year

    columns: list[tuple[int, int, int]] = []
    for col in range(2, frame.shape[1]):
        year = years.get(col)
        month = parse_month_es(frame.iat[1, col])
        if year and month:
            columns.append((col, year, month))
    return columns


def _clean_description(value: str) -> str:
    return re.sub(r"^[·\s]+", "", value).strip()


def load_icc(spec: SourceSpec, raw_dir: Path) -> list[Record]:
    path = raw_dir / spec.filename
    if not path.exists():
        raise FileNotFoundError(f"No existe {path}; ejecute primero la adquisición de datos.")

    frame = pd.read_excel(path, header=None)
    month_columns = _month_columns(frame)
    if not month_columns:
        raise ValueError(f"{spec.filename}: no se encontraron columnas mensuales")

    records: list[Record] = []
    current_stage: str | None = None

    for row_index in range(2, frame.shape[0]):
        raw_description = clean_text(frame.iat[row_index, 0])
        level = clean_text(frame.iat[row_index, 1])
        if not raw_description or not level:
            continue

        description = _clean_description(raw_description)
        if level == "Etapa":
            current_stage = description
        context = current_stage if level == "Recurso" else None

        for col, year, month in month_columns:
            value, _ = parse_number(frame.iat[row_index, col])
            if value is None:
                continue
            record_date = date(year, month, 1)
            records.append(
                Record(
                    id=f"{spec.id}-{row_index:03d}-{year}{month:02d}",
                    source="ICC",
                    source_group="ICC",
                    dataset=spec.id,
                    item=description,
                    category="Vivienda Social Básica",
                    metric="Índice ICC",
                    value_kind="index",
                    value=value,
                    unit="Vivienda social básica",
                    metric_unit="Índice (base 2025 = 100)",
                    currency=None,
                    date=record_date.isoformat(),
                    date_raw=f"{year}-{month:02d}",
                    date_status="valid",
                    year=year,
                    month=month,
                    region="Región I",
                    level=level,
                    context=context,
                    status=spec.status,
                    extra={"indexBase": "2025 = 100"},
                )
            )

    return records
