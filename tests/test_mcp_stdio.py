"""Compare the documented stdio server with the same snapshot served over HTTP."""

import asyncio
import json
import shutil
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi.testclient import TestClient
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from engine import config
from engine.api import app

ROOT = Path(__file__).resolve().parents[1]
LIST = "list_enabled_aggregates"
RECEIPT = "get_aggregate_receipt"
MISSING = object()


def _read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _snapshot_files(directory):
    return {
        path.relative_to(directory): (path.read_bytes(), path.stat().st_mtime_ns)
        for path in directory.rglob("*")
        if path.is_file()
    }


@asynccontextmanager
async def _session(tmp_path):
    project = tmp_path / "stdio_project"
    shutil.copytree(ROOT / "engine", project / "engine", ignore=shutil.ignore_patterns("__pycache__"))
    (project / "mcp").mkdir()
    shutil.copyfile(ROOT / "mcp/server.py", project / "mcp/server.py")
    snapshot = project / "stores/public_snapshot"
    shutil.copytree(config.PUBLIC_DIR, snapshot)
    before = _snapshot_files(snapshot)
    parameters = StdioServerParameters(
        command=sys.executable, args=["mcp/server.py"], cwd=project
    )
    async with stdio_client(parameters) as (reader, writer):
        async with ClientSession(reader, writer, read_timeout_seconds=15) as session:
            await session.initialize()
            yield session
    assert _snapshot_files(snapshot) == before
    assert not (project / "stores/review_store").exists()


async def _call(session, name, **arguments):
    result = await session.call_tool(name, arguments)
    assert not result.is_error, (name, arguments, result)
    assert isinstance(result.structured_content, dict), (name, arguments, result)
    return result.structured_content


def _compare(mismatches, case_id, path, expected, actual):
    if isinstance(expected, dict) and isinstance(actual, dict):
        for key in sorted(expected.keys() | actual.keys()):
            _compare(
                mismatches, case_id, f"{path}.{key}",
                expected.get(key, MISSING), actual.get(key, MISSING),
            )
    elif isinstance(expected, list) and isinstance(actual, list):
        for index in range(max(len(expected), len(actual))):
            _compare(
                mismatches, case_id, f"{path}[{index}]",
                expected[index] if index < len(expected) else MISSING,
                actual[index] if index < len(actual) else MISSING,
            )
    elif type(expected) is not type(actual) or expected != actual:
        wanted = "<missing>" if expected is MISSING else repr(expected)
        received = "<missing>" if actual is MISSING else repr(actual)
        mismatches.append(f"{case_id} {path}: expected {wanted}, actual {received}")


def _metadata(record):
    entity = record["entity"]
    display = entity.get("display") or {}
    license_info = entity.get("license") or {}
    return {
        **{key: record[key] for key in ("case_id", "state", "state_text", "published_at_utc")},
        "title": entity.get("title") or record["label"],
        **{key: display.get(key) for key in ("period", "base", "unit")},
        **{key: entity.get(key) for key in ("source_url", "downloaded_at_utc", "sha256")},
        "license": {key: license_info.get(key) for key in ("id", "attribution")},
        "decision_basis_digest": record["digest"],
    }


def _series_identity(series):
    return {key: series.get(key) for key in ("series_id", "label", "base")}


def _expected_listing(record):
    entity = record["entity"]
    return {
        **_metadata(record),
        "topic": entity.get("topic"),
        "series": [
            {
                **_series_identity(series),
                "comparable": series.get("comparable", True),
                "periods": [point["period"] for point in series["points"]],
            }
            for series in entity.get("series", [])
        ],
    }


def _expected_receipt_metadata(record):
    return {
        **_metadata(record),
        "series": [
            {
                **_series_identity(series),
                "unit": series.get("unit"),
                "periods": len(series["points"]),
            }
            for series in record["entity"].get("series", [])
        ],
    }


def _check_blocked(mismatches, case_id, payload):
    expected = {"case_id": case_id, "status": "bloqueada", "code": "no_publicado"}
    _compare(mismatches, case_id, "blocked", expected, {
        key: value for key, value in payload.items() if key != "message"
    })


def test_seeded_snapshot_over_stdio(seeded, tmp_path):
    index = _read_json(config.PUBLIC_DIR / "index.json")
    entries = index["aggregates"]
    case_ids = [entry["case_id"] for entry in entries]
    assert len(case_ids) == len(set(case_ids)) == 4
    mismatches = []

    async def check_stdio():
        async with _session(tmp_path) as session:
            discovery = await session.list_tools()
            assert discovery.next_cursor is None
            assert sorted(tool.name for tool in discovery.tools) == sorted([LIST, RECEIPT])
            schemas = {tool.name: tool.input_schema for tool in discovery.tools}
            assert schemas[LIST]["type"] == "object"
            assert schemas[LIST].get("properties", {}) == {}
            assert schemas[LIST].get("required", []) == []
            assert schemas[RECEIPT]["type"] == "object"
            assert set(schemas[RECEIPT]["properties"]) == {"case_id"}
            assert schemas[RECEIPT]["properties"]["case_id"]["type"] == "string"
            assert schemas[RECEIPT]["required"] == ["case_id"]

            listing = await _call(session, LIST)
            _compare(mismatches, "<snapshot>", "listing.repeat", listing, await _call(session, LIST))
            receipts = {}
            for case_id in case_ids:
                payload = await _call(session, RECEIPT, case_id=case_id)
                receipts[case_id] = payload
                repeated = await _call(session, RECEIPT, case_id=case_id)
                _compare(mismatches, case_id, "lookup.repeat", payload, repeated)

            for case_id in ("csv_grano_duplicado", "unknown-case"):
                payload = await _call(session, RECEIPT, case_id=case_id)
                _check_blocked(mismatches, case_id, payload)
                repeated = await _call(session, RECEIPT, case_id=case_id)
                _compare(mismatches, case_id, "blocked.repeat", payload, repeated)
            return listing, receipts

    listing, receipts = asyncio.run(check_stdio())
    _compare(mismatches, "<snapshot>", "listing.snapshot_id", index["snapshot_id"], listing.get("snapshot_id", MISSING))
    _compare(mismatches, "<snapshot>", "listing.total", len(case_ids), listing.get("total", MISSING))
    listed = listing.get("aggregates", [])
    _compare(mismatches, "<snapshot>", "listing.case_ids", case_ids, [item.get("case_id") for item in listed])
    by_id = {item.get("case_id"): item for item in listed}

    with TestClient(app) as client:
        http_index = client.get("/public").raise_for_status().json()
        _compare(mismatches, "<snapshot>", "http.snapshot_id", listing.get("snapshot_id", MISSING), http_index["snapshot_id"])
        _compare(mismatches, "<snapshot>", "http.case_ids", case_ids, [item["case_id"] for item in http_index["aggregates"]])
        http_by_id = {item["case_id"]: item for item in http_index["aggregates"]}
        for entry in entries:
            case_id = entry["case_id"]
            record = _read_json(config.PUBLIC_DIR / entry["file"])
            receipt = _read_json(config.PUBLIC_DIR / "receipts" / f"{case_id}.json")
            listing_item = by_id.get(case_id, {})
            lookup = receipts[case_id]
            expected_lookup = {
                "status": "ok", "case_id": case_id,
                "metadata": _expected_receipt_metadata(record), "receipt": receipt,
            }
            _compare(mismatches, case_id, "listing", _expected_listing(record), listing_item)
            _compare(mismatches, case_id, "lookup", expected_lookup, {
                key: value for key, value in lookup.items() if key != "notice"
            })
            _compare(
                mismatches, case_id, "lookup.metadata.decision_basis_digest",
                (lookup.get("receipt") or {}).get("technical_payload", {}).get("digest", MISSING),
                (lookup.get("metadata") or {}).get("decision_basis_digest", MISSING),
            )

            http_item = http_by_id.get(case_id, {})
            shared_fields = {
                "case_id": "case_id", "title": "title", "state": "state",
                "state_text": "state_text", "period": "period", "topic": "topic",
                "sha256": "sha256", "digest": "decision_basis_digest",
            }
            for http_key, listing_key in shared_fields.items():
                _compare(mismatches, case_id, f"http.index.{http_key}",
                         listing_item.get(listing_key, MISSING), http_item.get(http_key, MISSING))
            _compare(mismatches, case_id, "http.index.series_count",
                     len(listing_item.get("series", [])), http_item.get("series_count", MISSING))

            detail = client.get(f"/public/{case_id}").raise_for_status().json()
            _compare(mismatches, case_id, "http.detail.aggregate", record, detail["aggregate"])
            _compare(mismatches, case_id, "http.detail.receipt", lookup.get("receipt", MISSING), detail["receipt"])

    for name, payload in [("listing", listing), *receipts.items()]:
        for marker in ("private_evidence", "justifications", "review_store"):
            assert marker not in json.dumps(payload), (name, marker)
    assert not mismatches, "\n".join(mismatches)


def test_empty_snapshot_over_stdio(tmp_path):
    mismatches = []

    async def check_stdio():
        async with _session(tmp_path) as session:
            listing = await _call(session, LIST)
            _compare(mismatches, "<empty snapshot>", "listing", {
                "snapshot_id": None, "total": 0, "aggregates": [],
            }, {key: value for key, value in listing.items() if key != "notice"})
            for case_id in ("ipc_empalme", "unknown-case"):
                _check_blocked(mismatches, case_id, await _call(session, RECEIPT, case_id=case_id))

    asyncio.run(check_stdio())
    assert not mismatches, "\n".join(mismatches)
