"""P0.2: identity by SHA-256."""

from __future__ import annotations

from idt import config, engine
from idt.canonical import file_sha256
from idt.model import WARNING, FAILURE


def test_same_bytes_with_incompatible_identity_fails():
    result = engine.validate("dup_identidad", write_receipt=False)
    finding = next(f for f in result.findings if f.rule_id == "ID-01")
    assert finding.status == FAILURE
    assert result.entity["same_bytes"] is True
    assert set(finding.evidence["mismatched_fields"]) == {"dataset", "title"}
    assert result.state == "no_habilitado"


def test_documented_exception_becomes_warning(seeded):
    result = engine.validate("dup_identidad_excepcion", write_receipt=False)
    finding = next(f for f in result.findings if f.rule_id == "ID-01")
    assert finding.status == WARNING
    assert finding.justified is True
    assert finding.evidence["policy"]["policy"] == "POL-DUP-2026-01"
    assert result.state in ("en_revision", "habilitado_para_consulta")


def test_both_fixtures_have_same_bytes():
    a = file_sha256(config.FIXTURE_DIR / "identidad_a.csv")
    b = file_sha256(config.FIXTURE_DIR / "identidad_b.csv")
    assert a == b


def test_fixture_hash_matches_manifest():
    item = config.manifest_item("fix-identidad-a")
    assert file_sha256(config.ROOT / item["path"]) == item["sha256"]
