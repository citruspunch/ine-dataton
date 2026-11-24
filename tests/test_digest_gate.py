"""Reproducible digest, human gate and invalidation."""

from __future__ import annotations

import json

import pytest

from idt import config, engine, gate
from idt.model import WARNING, FAILURE, Finding, OK, derive_state


def test_two_runs_give_same_digest():
    first = engine.validate("ipc_empalme", write_receipt=False)
    second = engine.validate("ipc_empalme", write_receipt=False)
    assert first.digests["validation_digest"] == second.digests["validation_digest"]


def test_digest_changes_when_profile_changes():
    profile = config.load_profile("ipc_empalme_republica")
    other = json.loads(json.dumps(profile))
    other["version"] = "9.9.9"
    result = engine.validate("ipc_empalme", write_receipt=False)
    rules = config.load_rules()
    files = {"ine-ipc-empalme": result.entity["sha256"]}
    assert engine._basis_digest(files, profile, rules, result.findings) != (
        engine._basis_digest(files, other, rules, result.findings)
    )


def test_digest_does_not_depend_on_timestamps():
    result = engine.validate("ipc_empalme", write_receipt=False)
    payload = json.dumps(result.to_public_dict(), sort_keys=True)
    assert "generated_at_utc" not in payload
    assert "decided_at_utc" not in payload


def test_receipt_separates_payload_and_log(seeded):
    path = config.RECEIPT_DIR / "ipc_empalme.json"
    receipt = json.loads(path.read_text(encoding="utf-8"))
    assert "technical_payload" in receipt
    assert receipt["decision_log"] is not None
    assert (
        receipt["technical_payload"]["digest"]
        == engine.validate("ipc_empalme", write_receipt=False).digests[
            "validation_digest"
        ]
    )
    assert "comparisons" in receipt["technical_payload"]
    assert receipt["technical_payload"]["comparisons"]


def test_public_receipt_has_no_private_evidence(seeded):
    path = config.PUBLIC_DIR / "receipts" / "ipc_empalme.json"
    receipt = json.loads(path.read_text(encoding="utf-8"))
    assert "private_evidence" not in json.dumps(receipt)


def test_state_without_license_is_closed():
    assert (
        derive_state(
            [], license_verified=False, gate_approved=False, warnings_justified=True
        )
        == "cerrado"
    )


def test_state_with_critical_failure_is_not_enabled():
    finding = Finding("X-01", "t", FAILURE, True, "m")
    assert derive_state([finding], True, True, True) == "no_habilitado"


def test_state_all_ok_and_gate_is_enabled():
    finding = Finding("X-01", "t", OK, True, "m")
    assert derive_state([finding], True, True, True) == "habilitado_para_consulta"
    assert derive_state([finding], True, False, True) == "en_revision"


def test_unjustified_warning_stays_in_review():
    warning = Finding("X-01", "t", WARNING, True, "m", justified=False)
    assert derive_state([warning], True, True, False) == "en_revision"


# --------------------------------------------------------------------------
# Gate
# --------------------------------------------------------------------------


def test_gate_rejects_failing_case(sandbox):
    with pytest.raises(gate.GateError) as exc:
        gate.promote("dup_identidad", "Revisor", "Intento sobre un caso en falla.")
    assert "ID-01" in str(exc.value)


def test_gate_rejects_unevaluated_critical_rules(sandbox):
    result = engine.validate("xlsx_hoja_inesperada", write_receipt=False)
    problems = gate.blocking_reasons(result)
    assert any("no evaluadas" in p or "no_evaluado" in p for p in problems)


def test_gate_accepts_justified_exception(sandbox):
    result = engine.validate("dup_identidad_excepcion", write_receipt=False)
    assert gate.blocking_reasons(result) == []


def test_gate_requires_operator_and_rationale(sandbox):
    with pytest.raises(gate.GateError):
        gate.decide("csv_ok", "", "motivo suficientemente largo", "aprobar")
    with pytest.raises(gate.GateError):
        gate.decide("csv_ok", "Revisor", "corto", "aprobar")


def test_rejection_does_not_publish(sandbox):
    gate.decide("csv_ok", "Revisor", "Revisión insuficiente para publicar.", "rechazar")
    assert not gate.aggregate_path("csv_ok").exists()
    decision = config.latest_decision("csv_ok")
    assert decision["gate_decision"] == "rechazar"


def test_approval_publishes_and_writes_receipt(sandbox):
    gate.promote("ipc_empalme", "Revisor", "Cotejo contra la ficha oficial.")
    assert gate.aggregate_path("ipc_empalme").exists()
    receipt = json.loads(
        (config.PUBLIC_DIR / "receipts" / "ipc_empalme.json").read_text(
            encoding="utf-8"
        )
    )
    assert receipt["decision_log"]["gate_decision"] == "habilitado"
    assert (
        receipt["technical_payload"]["digest"]
        == engine.validate("ipc_empalme", write_receipt=False).digests[
            "validation_digest"
        ]
    )


def test_justified_warning_lifts_gate_block(sandbox):
    result = engine.validate("dup_identidad", write_receipt=False)
    assert gate.blocking_reasons(result)
    final = gate.decide(
        "dup_identidad",
        "Revisor",
        "Se documenta la reutilización intencional del mismo archivo.",
        "aprobar_con_excepcion",
        justifications={
            "ID-01": {
                "owner": "Revisor de publicaciones",
                "reason": "Reutilización intencional para dos series de eventos.",
                "policy": "POL-DUP-TEST",
            }
        },
    )
    assert final.state == "habilitado_para_consulta"
    assert final.comparisons == []


# --------------------------------------------------------------------------
# Invalidation
# --------------------------------------------------------------------------


def test_simulation_invalidates_decision_and_withdraws_aggregate(seeded):
    assert gate.aggregate_path("ipc_empalme").exists()
    before = config.latest_decision("ipc_empalme")["decision_basis_digest"]

    profile = config.load_profile("ipc_empalme_republica")
    profile["version"] = f"{profile['version']}+sim"
    config.save_override("ipc_empalme", profile, "prueba de invalidación")

    after = engine.validate("ipc_empalme", write_receipt=False).digests[
        "validation_digest"
    ]
    assert before != after

    report = {e["case_id"]: e for e in gate.verify()}
    assert report["ipc_empalme"]["quarantined"] is True
    assert not gate.aggregate_path("ipc_empalme").exists()
    assert (config.QUARANTINE_DIR / "ipc_empalme.json").exists()


def test_removing_simulation_restores_digest(seeded):
    profile = config.load_profile("ipc_empalme_republica")
    original = engine.validate("ipc_empalme", write_receipt=False).digests[
        "validation_digest"
    ]
    profile["version"] = f"{profile['version']}+sim"
    config.save_override("ipc_empalme", profile, "prueba")
    config.clear_override("ipc_empalme")
    assert (
        engine.validate("ipc_empalme", write_receipt=False).digests["validation_digest"]
        == original
    )


def test_verify_keeps_supported_aggregates(seeded):
    report = gate.verify()
    assert not [e for e in report if e["quarantined"]]
    for entry in report:
        if entry["decision_valid"]:
            assert entry["in_public_snapshot"], entry["case_id"]
