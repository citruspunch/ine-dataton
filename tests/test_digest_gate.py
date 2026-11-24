"""Digest reproducible, gate humano e invalidación."""

from __future__ import annotations

import json

import pytest

from idt import config, engine, gate
from idt.model import ADVERTENCIA, FALLA, Finding, OK, derive_state


def test_dos_ejecuciones_dan_el_mismo_digest():
    first = engine.validate("ipc_empalme", write_receipt=False)
    second = engine.validate("ipc_empalme", write_receipt=False)
    assert first.digests["validation_digest"] == second.digests["validation_digest"]


def test_el_digest_cambia_si_cambia_el_perfil():
    profile = config.load_profile("ipc_empalme_republica")
    other = json.loads(json.dumps(profile))
    other["version"] = "9.9.9"
    result = engine.validate("ipc_empalme", write_receipt=False)
    rules = config.load_rules()
    files = {"ine-ipc-empalme": result.entity["sha256"]}
    assert engine._basis_digest(files, profile, rules, result.findings) != (
        engine._basis_digest(files, other, rules, result.findings)
    )


def test_el_digest_no_depende_de_timestamps():
    result = engine.validate("ipc_empalme", write_receipt=False)
    payload = json.dumps(result.to_public_dict(), sort_keys=True)
    assert "generated_at_utc" not in payload
    assert "decided_at_utc" not in payload


def test_el_recibo_separa_payload_y_bitacora(seeded):
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


def test_el_recibo_publico_no_lleva_evidencia_privada(seeded):
    path = config.PUBLIC_DIR / "receipts" / "ipc_empalme.json"
    receipt = json.loads(path.read_text(encoding="utf-8"))
    assert "private_evidence" not in json.dumps(receipt)


def test_estado_sin_licencia_es_cerrado():
    assert (
        derive_state(
            [], license_verified=False, gate_approved=False, warnings_justified=True
        )
        == "cerrado"
    )


def test_estado_con_falla_critica_es_no_habilitado():
    finding = Finding("X-01", "t", FALLA, True, "m")
    assert derive_state([finding], True, True, True) == "no_habilitado"


def test_estado_con_todo_ok_y_gate_es_habilitado():
    finding = Finding("X-01", "t", OK, True, "m")
    assert derive_state([finding], True, True, True) == "habilitado_para_consulta"
    assert derive_state([finding], True, False, True) == "en_revision"


def test_advertencia_sin_justificar_deja_en_revision():
    warning = Finding("X-01", "t", ADVERTENCIA, True, "m", justified=False)
    assert derive_state([warning], True, True, False) == "en_revision"


# --------------------------------------------------------------------------
# Gate
# --------------------------------------------------------------------------


def test_el_gate_rechaza_un_caso_con_falla(sandbox):
    with pytest.raises(gate.GateError) as exc:
        gate.promote("dup_identidad", "Revisor", "Intento sobre un caso en falla.")
    assert "ID-01" in str(exc.value)


def test_el_gate_rechaza_reglas_criticas_no_evaluadas(sandbox):
    result = engine.validate("xlsx_hoja_inesperada", write_receipt=False)
    problems = gate.blocking_reasons(result)
    assert any("no evaluadas" in p or "no_evaluado" in p for p in problems)


def test_el_gate_acepta_la_excepcion_justificada(sandbox):
    result = engine.validate("dup_identidad_excepcion", write_receipt=False)
    assert gate.blocking_reasons(result) == []


def test_el_gate_exige_responsable_y_motivo(sandbox):
    with pytest.raises(gate.GateError):
        gate.decide("csv_ok", "", "motivo suficientemente largo", "aprobar")
    with pytest.raises(gate.GateError):
        gate.decide("csv_ok", "Revisor", "corto", "aprobar")


def test_rechazar_no_publica(sandbox):
    gate.decide("csv_ok", "Revisor", "Revisión insuficiente para publicar.", "rechazar")
    assert not gate.aggregate_path("csv_ok").exists()
    decision = config.latest_decision("csv_ok")
    assert decision["gate_decision"] == "rechazar"


def test_aprobar_publica_y_deja_recibo(sandbox):
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


def test_la_advertencia_justificada_en_el_gate_levanta_el_bloqueo(sandbox):
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
# Invalidación
# --------------------------------------------------------------------------


def test_simulacion_invalida_la_decision_y_retira_el_agregado(seeded):
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


def test_retirar_la_simulacion_restaura_el_digest(seeded):
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


def test_verify_no_retira_agregados_sostenidos(seeded):
    report = gate.verify()
    assert not [e for e in report if e["quarantined"]]
    for entry in report:
        if entry["decision_valid"]:
            assert entry["in_public_snapshot"], entry["case_id"]
