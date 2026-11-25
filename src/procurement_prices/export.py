"""Write clean Parquet/JSON artifacts and the web-facing data bundle."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .config import PROCESSED_DIR, WEB_DATA_DIR
from .model import Record
from .provenance import utc_now


def _ordered(records: list[Record], order: list[str]) -> list[Record]:
    positions = {group: index for index, group in enumerate(order)}
    return sorted(
        records,
        key=lambda record: (
            positions.get(record.source_group, 99),
            record.date or "0000-00-00",
            record.item,
        ),
    )


def _write_json(path: Path, payload: Any, *, compact: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if compact:
        text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    else:
        text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False)
    path.write_text(text + "\n", encoding="utf-8")


def _parquet_frame(records: list[Record]) -> pd.DataFrame:
    rows = []
    for record in records:
        public = record.to_public()
        rows.append(
            {
                "id": public["id"],
                "source": public["source"],
                "source_group": public["sourceGroup"],
                "dataset": public["dataset"],
                "item": public["item"],
                "category": public["category"],
                "metric": public["metric"],
                "unit": public["unit"],
                "value": public["value"],
                "value_kind": public["valueKind"],
                "currency": public["currency"],
                "date": public["date"],
                "date_raw": public["dateRaw"],
                "date_status": public["dateStatus"],
                "year": public["year"],
                "month": public["month"],
                "region": public["region"],
                "level": public["level"],
                "context": public["context"],
                "nog": public["nog"],
                "description": public["description"],
                "status": public["status"],
                "flags": "|".join(public["flags"]),
                "duplicate_of": public.get("duplicateOf"),
                "search_text": public["s"],
                "extra_json": json.dumps(record.extra, ensure_ascii=False)
                if record.extra
                else None,
            }
        )
    return pd.DataFrame(rows)


def write_outputs(
    records: list[Record],
    summary: dict[str, Any],
    manifest: dict[str, Any],
    catalog: dict[str, Any],
    dictionary: list[dict[str, Any]],
    order: list[str],
) -> dict[str, Path]:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)
    ordered = _ordered(records, order)

    parquet_path = PROCESSED_DIR / "records.parquet"
    _parquet_frame(ordered).to_parquet(parquet_path, index=False, compression="zstd")

    summary_payload = {"generatedAt": utc_now(), **summary}
    manifest_payload = {"generatedAt": utc_now(), **manifest}

    _write_json(PROCESSED_DIR / "summary.json", summary_payload)
    _write_json(PROCESSED_DIR / "manifest.json", manifest_payload)
    _write_json(PROCESSED_DIR / "dictionary.json", dictionary)

    _write_json(WEB_DATA_DIR / "summary.json", summary_payload)
    _write_json(WEB_DATA_DIR / "manifest.json", manifest_payload)
    _write_json(WEB_DATA_DIR / "catalog.json", catalog, compact=True)
    _write_json(WEB_DATA_DIR / "dictionary.json", dictionary)

    # The search index is rebuilt in the Next.js server from the record
    # fields, so the shipped JSON stays smaller and the Parquet keeps the
    # explicit `search_text` column for offline audit.
    web_records = []
    for record in ordered:
        public = record.to_public()
        public.pop("s", None)
        web_records.append(public)
    _write_json(WEB_DATA_DIR / "records.json", web_records, compact=True)

    return {
        "parquet": parquet_path,
        "summary": WEB_DATA_DIR / "summary.json",
        "manifest": WEB_DATA_DIR / "manifest.json",
        "records": WEB_DATA_DIR / "records.json",
        "catalog": WEB_DATA_DIR / "catalog.json",
    }
