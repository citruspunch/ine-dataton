"""La puerta pública: solo snapshot público, nunca evidencia privada."""

from __future__ import annotations

import json

import pytest

from idt import config, engine, gate, public_api


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


def test_listar_solo_agregados_habilitados(seeded):
    listed = public_api.listar_agregados_habilitados()
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


def test_un_caso_no_publicado_no_existe_para_la_consulta(seeded):
    assert public_api.get_aggregate("csv_grano_duplicado") is None
    with pytest.raises(public_api.PublicError) as exc:
        public_api.require_aggregate("csv_grano_duplicado")
    assert exc.value.code == "no_publicado"


def test_el_agregado_solo_publica_los_periodos_revisados(seeded):
    aggregate = public_api.require_aggregate("ipc_empalme")
    for series in aggregate["entity"]["series"]:
        assert {p["period"] for p in series["points"]} == {"2024-12", "2025-01"}


def test_no_hay_evidencia_privada_en_el_snapshot_publico(seeded):
    directory = config.PUBLIC_DIR
    for path in directory.rglob("*.json"):
        text = path.read_text(encoding="utf-8")
        assert "private_evidence" not in text, path.name
        assert "computed_pct_rounded" not in text, path.name
        assert "0.6738" not in text, path.name


def test_el_recibo_publico_separa_payload_y_bitacora(seeded):
    receipt = public_api.get_receipt("ipc_empalme")
    assert receipt["technical_payload"]["digest"]
    assert receipt["decision_log"]["gate_decision"] == "habilitado"
    assert "private_evidence" not in json.dumps(receipt)


def test_la_puerta_publica_rechaza_rutas_fuera_del_snapshot(seeded, tmp_path):
    outside = config.REVIEW_DIR / "cases.json"
    with pytest.raises(public_api.PublicError) as exc:
        public_api._safe(config.PUBLIC_DIR, "..", "review_store", "cases.json")
    assert exc.value.code == "acceso_denegado"
    assert public_api.get_aggregate("../review_store/cases") is None
    assert public_api.get_receipt("../../etc/passwd") is None


def test_el_snapshot_publico_no_menciona_la_carpeta_privada(seeded):
    for path in config.PUBLIC_DIR.rglob("*"):
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="ignore")
            assert "review_store" not in text, path.name


def test_la_serie_ipc_coincide_con_el_archivo_oficial(seeded):
    data = public_api.consultar_serie_ipc("2024-12", "2025-01")
    values = {p["period"]: p["value"] for p in data["points"]}
    assert values["2025-01"] == pytest.approx(101.017579223309, abs=1e-12)
    assert values["2024-12"] == pytest.approx(100.513540673814, abs=1e-9)


def test_consulta_publica_sin_agregados(sandbox):
    assert public_api.listar_agregados_habilitados() == []
    with pytest.raises(public_api.PublicError):
        public_api.consultar_serie_ipc("2024-01", "2025-12")
