from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine import config, gate  # noqa: E402
from fixtures_builder import write_fixtures  # noqa: E402

PROMOTIONS = ["ipc_empalme", "ipc_regional", "csv_ok", "dup_identidad_excepcion"]

TEST_JUSTIFICATIONS = {
    "note": "Justificaciones de la suite de pruebas.",
    "justifications": {
        "dup_identidad_excepcion": {
            "ID-01": {
                "policy": "POL-DUP-2026-01",
                "owner": "Revisor de publicaciones (prueba)",
                "date": "2026-11-24",
                "reason": "Reutilización intencional documentada.",
            }
        }
    },
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest_item(spec: dict, path: Path) -> dict:
    return {
        "id": spec["id"],
        "kind": spec["kind"],
        "synthetic": spec["kind"] == "synthetic",
        "source_id": spec.get("source_id"),
        "dataset_id": spec.get("dataset_id"),
        "resource_id": spec.get("resource_id"),
        "title": spec["title"],
        "path": str(path),
        "source_url": spec.get("source_url"),
        "downloaded_at_utc": "2026-11-23T12:00:00Z",
        "downloaded_at_source": "prueba",
        "bytes": path.stat().st_size,
        "sha256": _sha256(path),
        "profile": spec.get("profile"),
        "license": spec["license"],
    }


def _build_manifest(fixtures_dir: Path) -> dict:
    """Real snapshot items plus the synthetic fixtures used only by the suite."""
    sources = json.loads(
        (ROOT / "tests" / "data" / "real" / "sources.json").read_text(encoding="utf-8")
    )
    items = []
    for spec in sources["items"]:
        path = ROOT / "tests" / "data" / "real" / Path(spec["path"]).name
        items.append(_manifest_item(spec, path))

    synthetic = json.loads(
        (ROOT / "tests" / "data" / "sources_synthetic.json").read_text(encoding="utf-8")
    )
    for spec in synthetic["items"]:
        path = fixtures_dir / Path(spec["path"]).name
        items.append(_manifest_item(spec, path))

    return {
        "snapshot_id": "snap-prueba",
        "prepared_at_utc": "2026-11-23T12:00:00Z",
        "note": "Manifiesto de la suite de pruebas.",
        "items": items,
    }


@pytest.fixture(autouse=True)
def sandbox(tmp_path, monkeypatch):
    """Redirect every writable path and every demo input to a temporary directory.

    The product ships without synthetic fixtures. The suite generates them here
    and points the engine at a test-only profile directory, cases file and
    manifest, so tests never touch the real snapshot.
    """
    review = tmp_path / "review_store"
    public = tmp_path / "public_snapshot"
    review.mkdir()
    public.mkdir()

    fixtures_dir = tmp_path / "fixtures"
    write_fixtures(fixtures_dir)

    profiles_dir = tmp_path / "engine_profiles"
    profiles_dir.mkdir()
    for directory in (ROOT / "profiles", ROOT / "tests" / "profiles"):
        for path in directory.glob("*.yaml"):
            shutil.copyfile(path, profiles_dir / path.name)

    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text(
        json.dumps(_build_manifest(fixtures_dir), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    cases_file = tmp_path / "cases.json"
    shutil.copyfile(ROOT / "tests" / "data" / "cases.json", cases_file)

    monkeypatch.setattr(config, "REVIEW_DIR", review)
    monkeypatch.setattr(config, "PUBLIC_DIR", public)
    monkeypatch.setattr(config, "RECEIPT_DIR", review / "receipts")
    monkeypatch.setattr(config, "DECISION_DIR", review / "decisions")
    monkeypatch.setattr(config, "UPLOAD_DIR", review / "uploads")
    monkeypatch.setattr(config, "OVERRIDE_DIR", review / "overrides")
    monkeypatch.setattr(config, "QUARANTINE_DIR", review / "quarantine")
    monkeypatch.setattr(config, "FIXTURE_DIR", fixtures_dir)
    monkeypatch.setattr(config, "PROFILE_DIR", profiles_dir)
    monkeypatch.setattr(config, "MANIFEST_FILE", manifest_file)
    monkeypatch.setattr(config, "CASES_FILE", cases_file)
    monkeypatch.setattr(
        config, "DECISIONS_FILE", review / "decisions" / "decisions.jsonl"
    )
    monkeypatch.setattr(config, "UPLOAD_REGISTRY", review / "uploads" / "manifest.json")
    monkeypatch.setattr(config, "JUSTIFICATION_FILE", review / "justifications.json")

    (review / "justifications.json").write_text(
        json.dumps(TEST_JUSTIFICATIONS, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture()
def seeded(sandbox):
    """Sandbox with the four cases approved for the test."""
    for case_id in PROMOTIONS:
        gate.promote(
            case_id,
            "Técnico de publicaciones (prueba)",
            "Aprobación registrada por la suite de pruebas.",
        )
    return sandbox
