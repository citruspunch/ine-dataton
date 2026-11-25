"""HTTP API: the surface the Next.js app consumes."""

from __future__ import annotations

import json
import shutil

import pytest
from fastapi.testclient import TestClient

from engine import config
from engine.api import app


@pytest.fixture()
def client(seeded):
    return TestClient(app)


@pytest.fixture()
def profiles_dir(tmp_path, monkeypatch):
    directory = tmp_path / "profiles"
    directory.mkdir()
    for path in config.PROFILE_DIR.glob("*.yaml"):
        shutil.copyfile(path, directory / path.name)
    monkeypatch.setattr(config, "PROFILE_DIR", directory)
    return directory


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_review_cases_lists_nine_cases(client):
    response = client.get("/review/cases")
    assert response.status_code == 200
    cases = response.json()["cases"]
    assert len(cases) == 9
    assert {case["id"] for case in cases} >= {"ipc_empalme", "csv_grano_duplicado"}


def test_review_detail_shape(client):
    data = client.get("/review/ipc_empalme").json()
    assert data["state"] == "habilitado_para_consulta"
    assert data["coverage"]["critical_evaluated"] == 8
    assert data["digest"]
    assert data["blocking"] == []
    assert {finding["rule_id"] for finding in data["findings"]} >= {
        "SNAP-01",
        "CONT-05",
    }


def test_review_detail_shows_private_comparison(client):
    data = client.get("/review/ipc_empalme").json()
    blocked = next(
        item
        for item in data["comparisons"]
        if item["comparison_id"] == "cruce_bases_e_f"
    )
    assert blocked["status"] == "bloqueada"
    assert blocked["private_evidence"]["computed_pct"] == pytest.approx(
        -0.673802, abs=1e-6
    )


def test_upload_then_gate_publishes(client, sandbox):
    content = (config.FIXTURE_DIR / "contrato_ok.csv").read_bytes()
    upload = client.post(
        "/review/upload",
        files={"file": ("ok.csv", content, "text/csv")},
        data={"profile": "contrato_mensual_v1", "license": "cc-by"},
    )
    assert upload.status_code == 200
    case_id = upload.json()["case_id"]

    detail = client.get(f"/review/{case_id}").json()
    assert detail["state"] == "en_revision"
    assert detail["blocking"] == []

    gate = client.post(
        f"/review/{case_id}/gate",
        json={
            "operator": "Revisora QA",
            "rationale": "Contrato sintético cotejado contra el perfil declarado.",
            "decision": "aprobar",
        },
    )
    assert gate.status_code == 200
    assert gate.json()["state"] == "habilitado_para_consulta"
    assert client.get(f"/public/{case_id}").status_code == 200


def test_upload_without_license_closes_resource(client, sandbox):
    content = (config.FIXTURE_DIR / "contrato_ok.csv").read_bytes()
    upload = client.post(
        "/review/upload",
        files={"file": ("sin.csv", content, "text/csv")},
        data={"profile": "contrato_mensual_v1", "license": "sin-licencia"},
    )
    case_id = upload.json()["case_id"]
    assert client.get(f"/review/{case_id}").json()["state"] == "cerrado"


def test_gate_rejects_failing_case(client):
    response = client.post(
        "/review/dup_identidad/gate",
        json={
            "operator": "Revisor",
            "rationale": "Intento sobre un caso con falla crítica.",
            "decision": "aprobar",
        },
    )
    assert response.status_code == 409
    assert "ID-01" in response.json()["detail"]


def test_simulate_withdraws_and_undo_republishes(client):
    assert client.get("/public/ipc_empalme").status_code == 200
    simulate = client.post("/review/ipc_empalme/simulate")
    assert simulate.status_code == 200
    assert client.get("/public/ipc_empalme").status_code == 404

    undo = client.post("/review/ipc_empalme/simulate/undo")
    assert undo.status_code == 200
    assert undo.json()["republished"] is True
    assert client.get("/public/ipc_empalme").status_code == 200


def test_public_index_and_detail(client):
    index = client.get("/public").json()
    assert index["snapshot_id"]
    assert {item["case_id"] for item in index["aggregates"]} == {
        "ipc_empalme",
        "ipc_regional",
        "csv_ok",
        "dup_identidad_excepcion",
    }
    detail = client.get("/public/ipc_empalme").json()
    assert detail["aggregate"]["digest"]
    assert detail["receipt"]["decision_log"]["gate_decision"] == "habilitado"
    assert "private_evidence" not in json.dumps(detail)


def test_compare_valid_and_blocked(client):
    valid = client.post(
        "/public/ipc_empalme/compare",
        json={
            "series_a": "f",
            "period_a": "2024-12",
            "series_b": "f",
            "period_b": "2025-01",
        },
    ).json()
    assert valid["status"] == "ok"
    assert valid["published_pct"] == pytest.approx(0.501463, abs=1e-6)
    assert valid["published_cell"] == "G504"

    blocked = client.post(
        "/public/ipc_empalme/compare",
        json={
            "series_a": "e",
            "period_a": "2024-12",
            "series_b": "f",
            "period_b": "2025-01",
        },
    ).json()
    assert blocked["status"] == "bloqueada"
    assert blocked["code"] == "base_incompatible"
    assert "published_pct" not in blocked


def test_public_receipt_is_downloadable(client):
    response = client.get("/public/ipc_empalme/receipt.json")
    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    payload = response.json()
    assert set(payload) >= {"technical_payload", "decision_log"}


def test_profile_validation_reports_fields(client, profiles_dir):
    response = client.post(
        "/profiles/validate", json={"yaml": "profile_id: x\nkind: xlsx\n"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is False
    fields = {error["field"] for error in body["errors"]}
    assert {"expected_sheet", "schema", "grain", "dates", "comparability"} <= fields


def test_profile_creation_and_duplicate(client, profiles_dir):
    yaml_text = (profiles_dir / "contrato_mensual_v1.yaml").read_text(encoding="utf-8")
    duplicate = client.post("/profiles", json={"yaml": yaml_text})
    assert duplicate.status_code == 409

    created = client.post("/profiles", json={"yaml": yaml_text, "overwrite": True})
    assert created.status_code == 200
    assert created.json()["profile_id"] == "contrato_mensual_v1"

    listed = client.get("/profiles").json()["profiles"]
    assert all(profile["valid"] for profile in listed)


def test_profile_creation_rejects_bad_yaml(client, profiles_dir):
    response = client.post("/profiles", json={"yaml": "profile_id: [unclosed"})
    assert response.status_code == 422
    assert response.json()["detail"]["errors"][0]["field"] == "yaml"
