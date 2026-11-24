"""Interfaz web: bandeja, gate, comparador y exportaciones."""

from __future__ import annotations

import json
import re
import urllib.parse
from pathlib import Path

from idt import config


def _text(response) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", response.text))


def test_portada_y_bandeja(client):
    assert client.get("/").status_code == 200
    inbox = client.get("/review")
    assert inbox.status_code == 200
    assert "Bandeja de revisión técnica" in inbox.text


def test_detalle_de_revision_carga(client):
    page = client.get("/review/ipc_empalme")
    assert page.status_code == 200
    assert "Gate humano" in page.text
    assert "SNAP-01" in page.text
    assert "F504" in page.text


def test_la_revision_muestra_el_valor_bloqueado(client):
    page = _text(client.get("/review/ipc_empalme"))
    assert "-0,67%" in page
    assert "solo revisión" in page


def test_la_consulta_publica_no_muestra_el_valor_bloqueado(client):
    page = client.get("/a/ipc_empalme")
    assert page.status_code == 200
    assert "0,67" not in page.text
    assert "0.6738" not in page.text


def test_comparador_valido(client):
    response = client.post(
        "/a/ipc_empalme/compare",
        data={
            "series_a": "f",
            "period_a": "2024-12",
            "series_b": "f",
            "period_b": "2025-01",
        },
    )
    assert response.status_code == 200
    text = _text(response)
    assert "Variación mensual publicada" in text
    assert "+0,50%" in text
    assert "G504" in text


def test_comparador_bloquea_bases_distintas(client):
    response = client.post(
        "/a/ipc_empalme/compare",
        data={
            "series_a": "e",
            "period_a": "2024-12",
            "series_b": "f",
            "period_b": "2025-01",
        },
    )
    text = _text(response)
    assert "Comparación bloqueada" in text
    assert "Bases distintas" in text
    assert "0,67" not in text


def test_comparador_bloquea_recurso_sin_variacion(client):
    response = client.post(
        "/a/ipc_regional/compare",
        data={
            "series_a": "republica",
            "period_a": "2025-01",
            "series_b": "republica",
            "period_b": "2025-02",
        },
    )
    assert "Este recurso publica índices" in _text(response)


def test_ficha_tecnica_imprimible(client):
    page = client.get("/a/ipc_empalme/ficha")
    assert page.status_code == 200
    assert "Ficha técnica de validación" in page.text
    aggregate = json.loads(
        (config.PUBLIC_DIR / "aggregates" / "ipc_empalme.json").read_text(
            encoding="utf-8"
        )
    )
    assert aggregate["digest"] in page.text


def test_descarga_de_recibo(client):
    response = client.get("/a/ipc_empalme/receipt.json")
    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"]
    payload = response.json()
    assert set(payload) >= {"technical_payload", "decision_log"}
    assert "private_evidence" not in json.dumps(payload)


def test_caso_no_publicado_no_es_consultable(client):
    response = client.get("/a/csv_grano_duplicado", follow_redirects=False)
    assert response.status_code == 303


def test_flujo_completo_de_carga_y_gate(client, sandbox):
    content = (config.ROOT / "review_store/fixtures/contrato_ok.csv").read_bytes()
    upload = client.post(
        "/review/upload",
        files={"file": ("mi_contrato.csv", content, "text/csv")},
        data={"profile": "contrato_mensual", "license": "cc-by"},
        follow_redirects=False,
    )
    assert upload.status_code == 303
    location = upload.headers["location"].split("?")[0]
    assert client.get(location).status_code == 200

    gate = client.post(
        f"{location}/gate",
        data={
            "operator": "Revisora de publicaciones",
            "rationale": "Contrato sintético cotejado contra el perfil declarado.",
            "decision": "aprobar",
        },
        follow_redirects=False,
    )
    assert gate.status_code == 303
    index = json.loads((config.PUBLIC_DIR / "index.json").read_text(encoding="utf-8"))
    assert any(a["case_id"].startswith("up-") for a in index["aggregates"])


def test_carga_con_licencia_no_verificada_cierra_el_recurso(client, sandbox):
    content = (config.ROOT / "review_store/fixtures/contrato_ok.csv").read_bytes()
    upload = client.post(
        "/review/upload",
        files={"file": ("sin_licencia.csv", content, "text/csv")},
        data={"profile": "contrato_mensual", "license": "sin-licencia"},
        follow_redirects=False,
    )
    location = upload.headers["location"].split("?")[0]
    page = _text(client.get(location))
    assert "Cerrado por defecto" in page


def test_extension_no_aceptada(client, sandbox):
    response = client.post(
        "/review/upload",
        files={"file": ("datos.txt", b"hola", "text/plain")},
        data={"profile": "contrato_mensual", "license": "cc-by"},
        follow_redirects=False,
    )
    assert "extensión no aceptada" in urllib.parse.unquote(response.headers["location"])


def test_simulacion_retira_el_agregado_del_portal(client, sandbox):
    assert client.get("/a/ipc_empalme").status_code == 200
    client.post("/review/ipc_empalme/simulate", follow_redirects=False)
    assert client.get("/a/ipc_empalme", follow_redirects=False).status_code == 303
    sheet = _text(client.get("/review/ipc_empalme"))
    assert "simulación activa" in sheet

    client.post("/review/ipc_empalme/simulate/undo", follow_redirects=False)
    assert client.get("/a/ipc_empalme").status_code == 200


def test_gate_bloqueado_en_la_interfaz(client):
    page = _text(client.get("/review/csv_grano_duplicado"))
    assert "No habilitable todavía" in page
    assert "Registrar rechazo" in page
