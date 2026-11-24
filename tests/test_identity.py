"""P0.2: identidad por SHA-256."""

from __future__ import annotations

from idt import config, engine
from idt.canonical import file_sha256
from idt.model import ADVERTENCIA, FALLA


def test_mismos_bytes_identidad_incompatible_falla():
    result = engine.validate("dup_identidad", write_receipt=False)
    finding = next(f for f in result.findings if f.rule_id == "ID-01")
    assert finding.status == FALLA
    assert result.entity["same_bytes"] is True
    assert set(finding.evidence["mismatched_fields"]) == {"dataset", "title"}
    assert result.state == "no_habilitado"


def test_excepcion_documentada_pasa_a_advertencia(seeded):
    result = engine.validate("dup_identidad_excepcion", write_receipt=False)
    finding = next(f for f in result.findings if f.rule_id == "ID-01")
    assert finding.status == ADVERTENCIA
    assert finding.justified is True
    assert finding.evidence["policy"]["policy"] == "POL-DUP-2026-01"
    assert result.state in ("en_revision", "habilitado_para_consulta")


def test_los_dos_fixtures_tienen_los_mismos_bytes():
    a = file_sha256(config.FIXTURE_DIR / "identidad_a.csv")
    b = file_sha256(config.FIXTURE_DIR / "identidad_b.csv")
    assert a == b


def test_el_hash_del_fixture_coincide_con_el_manifiesto():
    item = config.manifest_item("fix-identidad-a")
    assert file_sha256(config.ROOT / item["path"]) == item["sha256"]
