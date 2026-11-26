"""MCP server: typed read-only tools and isolation from the private store."""

from __future__ import annotations

import asyncio
import inspect
import json
from pathlib import Path

import pytest

from engine import config, public_api

ROOT = Path(__file__).resolve().parent.parent


def test_server_exposes_two_read_only_tools():
    from engine import mcp_server

    tools = asyncio.run(mcp_server.server.list_tools())
    assert {tool.name for tool in tools} == {
        "list_enabled_aggregates",
        "get_aggregate_receipt",
    }


def test_no_period_comparison_tool():
    from engine import mcp_server

    tools = asyncio.run(mcp_server.server.list_tools())
    assert not any("compar" in tool.name for tool in tools)
    assert not hasattr(mcp_server, "query_ipc_period_comparison")


def test_list_enabled_aggregates(seeded):
    from engine import mcp_server

    data = mcp_server.list_enabled_aggregates()
    assert data["total"] == 4
    assert data["snapshot_id"]
    aggregates = data["aggregates"]
    for aggregate in aggregates:
        assert aggregate["decision_basis_digest"]
        assert aggregate["license"]["id"] in ("cc-by", "interno-fixture")
        assert "periods" in aggregate["series"][0] if aggregate["series"] else True


def test_get_aggregate_receipt(seeded):
    from engine import mcp_server

    data = mcp_server.get_aggregate_receipt("ipc_empalme")
    assert data["status"] == "ok"
    metadata = data["metadata"]
    assert metadata["source_url"].startswith("https://datos.ine.gob.gt/")
    assert metadata["downloaded_at_utc"]
    assert metadata["license"]["id"] == "cc-by"
    assert metadata["decision_basis_digest"]
    assert metadata["series"]
    receipt = data["receipt"]
    assert receipt["technical_payload"]["digest"] == metadata["decision_basis_digest"]
    assert receipt["decision_log"]["gate_decision"] == "habilitado"


def test_get_aggregate_receipt_blocks_unpublished(seeded):
    from engine import mcp_server

    data = mcp_server.get_aggregate_receipt("csv_grano_duplicado")
    assert data["status"] == "bloqueada"
    assert data["code"] == "no_publicado"
    assert "receipt" not in data


def test_no_aggregates_means_no_receipt(sandbox):
    from engine import mcp_server

    data = mcp_server.get_aggregate_receipt("ipc_empalme")
    assert data["status"] == "bloqueada"
    assert data["code"] == "no_publicado"


# --------------------------------------------------------------------------
# Isolation
# --------------------------------------------------------------------------


def test_mcp_server_does_not_import_engine_or_private_store():
    import ast

    source = (ROOT / "engine" / "mcp_server.py").read_text(encoding="utf-8")
    imported: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.ImportFrom):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)

    assert "public_api" in imported
    assert not imported & {"rules", "gate", "store", "config"}


def test_public_door_does_not_leave_snapshot(seeded):
    with pytest.raises(public_api.PublicError) as exc:
        public_api._safe(config.PUBLIC_DIR, "..", "review_store", "decisions")
    assert exc.value.code == "acceso_denegado"


def test_public_snapshot_has_no_private_decisions(seeded):
    for path in config.PUBLIC_DIR.rglob("*.json"):
        text = path.read_text(encoding="utf-8")
        assert "justifications" not in text


def test_tools_do_not_accept_paths(seeded):
    """No tool accepts a path: there is no way to ask for the review store."""
    from engine import mcp_server

    allowed = {
        "list_enabled_aggregates": set(),
        "get_aggregate_receipt": {"case_id"},
    }
    for name, expected in allowed.items():
        params = set(inspect.signature(getattr(mcp_server, name)).parameters)
        assert params == expected
        assert not params & {"path", "dir", "public_dir", "file", "url"}


def test_mcp_response_is_json_serializable(seeded):
    from engine import mcp_server

    payload = json.dumps(mcp_server.get_aggregate_receipt("ipc_empalme"))
    assert '"technical_payload"' in payload
