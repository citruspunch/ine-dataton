"""The public door: public snapshot only, never private evidence."""

from __future__ import annotations

import json

import pytest

from engine import config, gate, rules, public_api


def _walk_strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for key, value in node.items():
            yield str(key)
            yield from _walk_strings(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_strings(item)


def test_lists_only_enabled_aggregates(seeded):
    listed = public_api.list_enabled_aggregates()
    assert {a["case_id"] for a in listed} == {
        "ipc_empalme",
        "ipc_regional",
        "csv_ok",
        "dup_identidad_excepcion",
    }
    ipc = next(a for a in listed if a["case_id"] == "ipc_empalme")
    assert ipc["source_url"].startswith("https://datos.ine.gob.gt/")
    assert ipc["downloaded_at_utc"]
    assert ipc["license"]["id"] == "cc-by"
    assert ipc["decision_basis_digest"]


def test_unpublished_case_does_not_exist_for_consultation(seeded):
    assert public_api.get_aggregate("csv_grano_duplicado") is None
    with pytest.raises(public_api.PublicError) as exc:
        public_api.require_aggregate("csv_grano_duplicado")
    assert exc.value.code == "no_publicado"


def test_aggregate_publishes_only_reviewed_periods(seeded):
    aggregate = public_api.require_aggregate("ipc_empalme")
    for series in aggregate["entity"]["series"]:
        assert {p["period"] for p in series["points"]} == {"2024-12", "2025-01"}


def test_no_private_evidence_in_public_snapshot(seeded):
    directory = config.PUBLIC_DIR
    for path in directory.rglob("*.json"):
        text = path.read_text(encoding="utf-8")
        assert "private_evidence" not in text, path.name
        assert "computed_pct_rounded" not in text, path.name
        assert "0.6738" not in text, path.name


def test_public_receipt_separates_payload_and_log(seeded):
    receipt = public_api.get_receipt("ipc_empalme")
    assert receipt["technical_payload"]["digest"]
    assert receipt["decision_log"]["gate_decision"] == "habilitado"
    assert "private_evidence" not in json.dumps(receipt)


def test_public_door_rejects_paths_outside_snapshot(seeded, tmp_path):
    outside = config.REVIEW_DIR / "cases.json"
    with pytest.raises(public_api.PublicError) as exc:
        public_api._safe(config.PUBLIC_DIR, "..", "review_store", "cases.json")
    assert exc.value.code == "acceso_denegado"
    assert public_api.get_aggregate("../review_store/cases") is None
    assert public_api.get_receipt("../../etc/passwd") is None


def test_public_snapshot_does_not_mention_private_folder(seeded):
    for path in config.PUBLIC_DIR.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert "review_store" not in text, path.name


def test_public_consultation_without_aggregates(sandbox):
    assert public_api.list_enabled_aggregates() == []
    with pytest.raises(public_api.PublicError):
        public_api.require_aggregate("ipc_empalme")
