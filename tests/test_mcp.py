"""MCP server: typed tools and isolation from the private store."""

from __future__ import annotations

import asyncio
import inspect
import json
from pathlib import Path

import pytest

from engine import config, public_api

ROOT = Path(__file__).resolve().parent.parent


def test_server_exposes_two_tools():
    from engine import mcp_server

    tools = asyncio.run(mcp_server.server.list_tools())
    assert {tool.name for tool in tools} == {
        "list_enabled_aggregates",
        "query_ipc_period_comparison",
    }


def test_list_enabled_aggregates(seeded):
    from engine import mcp_server

    data = mcp_server.list_enabled_aggregates()
    assert data["total"] == 4
    assert data["snapshot_id"]
    for aggregate in data["agregados" if "agregados" in data else "aggregates"]:
        assert aggregate["decision_basis_digest"]
        assert aggregate["license"]["id"] in ("cc-by", "interno-fixture")


def test_query_ipc_period_comparison(seeded):
    from engine import mcp_server

    data = mcp_server.query_ipc_period_comparison("2024-12", "2025-01")
    assert data["status"] == "ok"
    assert data["published_pct"] == pytest.approx(0.501463, abs=1e-6)
    assert data["published_cell"] == "G504"
    assert data["digest"]


def test_query_returns_structured_block(seeded):
    from engine import mcp_server

    data = mcp_server.query_ipc_period_comparison("1990-01", "1990-06")
    assert data["status"] == "bloqueada"
    assert data["code"] == "periodo_no_publicado"
    assert "published_pct" not in data


def test_no_aggregates_means_no_figures(sandbox):
    from engine import mcp_server

    data = mcp_server.query_ipc_period_comparison("2024-12", "2025-01")
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
        "query_ipc_period_comparison": {"period_a", "period_b", "series"},
    }
    for name, expected in allowed.items():
        params = set(inspect.signature(getattr(mcp_server, name)).parameters)
        assert params == expected
        assert not params & {"path", "dir", "public_dir", "file", "url"}


def test_mcp_response_is_json_serializable(seeded):
    from engine import mcp_server

    payload = json.dumps(mcp_server.query_ipc_period_comparison("2024-12", "2025-01"))
    assert '"published_pct"' in payload
