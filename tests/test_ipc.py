"""Contract validation for the IPC profiles and their variables summary."""

from __future__ import annotations

import json

from engine import rules
from engine.model import OK


def test_full_ipc_contract():
    result = rules.validate("ipc_empalme", write_receipt=False)
    assert result.coverage["complete"]
    assert [f.status for f in result.findings] == [OK] * len(result.findings)
    assert (
        result.entity["sha256"]
        == "d0101e366ee6d6bb02345db64b8c725c0a4c65ee85aa800d751d41b8381664d4"
    )


def test_summary_reports_units_references_and_counts():
    result = rules.validate("ipc_empalme", write_receipt=False)
    summary = result.entity["variables_summary"]
    assert summary["row_count"] == 524
    columns = {column["name"]: column for column in summary["columns"]}
    assert columns["f_index"]["unit"] == "índice"
    assert columns["f_index"]["reference"] == "2024=100"
    assert columns["e_index"]["reference"] == "Diciembre 2023=100"
    assert columns["g_monthly"]["unit"] == "porcentaje"
    assert columns["g_monthly"]["nullable"] is True
    assert columns["f_index"]["valid_count"] == 524
    assert columns["f_index"]["null_count"] == 0
    assert columns["f_index"]["excluded_count"] == 0
    assert summary["coverage"]["period"] == "diciembre 2024 y enero 2025"
    assert "bases" in summary["coverage"]["notes"]


def test_public_payload_has_no_comparison_or_series_model():
    result = rules.validate("ipc_empalme", write_receipt=False)
    public = json.dumps(result.to_public_dict(), ensure_ascii=False)
    assert "comparisons" not in public
    assert "comparison_id" not in public
    assert "series" not in public
    assert "computed_pct" not in public
