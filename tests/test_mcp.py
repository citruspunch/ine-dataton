"""Servidor MCP: herramientas tipadas y aislamiento del almacén privado."""

from __future__ import annotations

import inspect
import json
from pathlib import Path

import pytest

from idt import config, public_api

ROOT = Path(__file__).resolve().parent.parent


def test_el_servidor_expone_dos_herramientas():
    import asyncio

    import mcp_server

    tools = asyncio.run(mcp_server.server.list_tools())
    assert {tool.name for tool in tools} == {
        "listar_agregados_habilitados",
        "consultar_serie_ipc",
    }


def test_listar_agregados_habilitados(seeded):
    import mcp_server

    data = mcp_server.listar_agregados_habilitados()
    assert data["total"] == 4
    assert data["snapshot_id"]
    for aggregate in data["agregados"]:
        assert aggregate["decision_basis_digest"]
        assert aggregate["license"]["id"] in ("cc-by", "interno-fixture")


def test_consultar_serie_ipc(seeded):
    import mcp_server

    data = mcp_server.consultar_serie_ipc("2024-01", "2025-12")
    assert data["status"] == "ok"
    assert [p["period"] for p in data["points"]] == ["2024-12", "2025-01"]
    assert data["points"][-1]["published_variation_pct"] == pytest.approx(
        0.5014633313243735, abs=1e-12
    )
    assert data["source_url"].startswith("https://datos.ine.gob.gt/")


def test_consultar_serie_devuelve_bloqueo_estructurado(seeded):
    import mcp_server

    data = mcp_server.consultar_serie_ipc("1990-01", "1990-06")
    assert data["status"] == "bloqueada"
    assert data["code"] == "periodo_no_publicado"
    assert "points" not in data


def test_sin_agregados_no_hay_cifras(sandbox):
    import mcp_server

    data = mcp_server.consultar_serie_ipc("2024-01", "2025-12")
    assert data["status"] == "bloqueada"
    assert data["code"] == "no_publicado"


# --------------------------------------------------------------------------
# Aislamiento
# --------------------------------------------------------------------------


def test_el_servidor_mcp_no_importa_el_motor_ni_el_almacen_privado():
    source = (ROOT / "mcp_server.py").read_text(encoding="utf-8")
    for forbidden in (
        "from idt import config, store",
        "from .store",
        "idt.gate",
        "idt.engine",
    ):
        assert forbidden not in source
    assert "public_api" in source


def test_la_puerta_publica_no_sale_del_snapshot(seeded):
    with pytest.raises(public_api.PublicError) as exc:
        public_api._safe(config.PUBLIC_DIR, "..", "review_store", "decisions")
    assert exc.value.code == "acceso_denegado"


def test_el_snapshot_publico_no_contiene_decisiones_privadas(seeded):
    for path in config.PUBLIC_DIR.rglob("*.json"):
        text = path.read_text(encoding="utf-8")
        assert "decision_id" not in text or "receipts" in str(path)
        assert "justifications" not in text


def test_las_herramientas_no_aceptan_rutas(seeded):
    """Ninguna herramienta recibe una ruta: no hay forma de pedir review_store."""
    import mcp_server

    for name in ("listar_agregados_habilitados", "consultar_serie_ipc"):
        signature = inspect.signature(getattr(mcp_server, name))
        params = set(signature.parameters)
        assert not params & {"path", "dir", "public_dir", "file", "url"}


def test_la_respuesta_mcp_es_json_serializable(seeded):
    import mcp_server

    payload = json.dumps(mcp_server.consultar_serie_ipc("2024-01", "2025-12"))
    assert '"published_variation_pct"' in payload
