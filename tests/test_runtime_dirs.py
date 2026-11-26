import json
import shutil

from fastapi.testclient import TestClient

from engine import config


def test_ensure_runtime_dirs_recreates_missing_layout(tmp_path, monkeypatch):
    data = tmp_path / "data"
    profiles = tmp_path / "profiles"
    review = tmp_path / "stores" / "review_store"
    public = tmp_path / "stores" / "public_snapshot"
    monkeypatch.setattr(config, "DATA_DIR", data)
    monkeypatch.setattr(config, "PROFILE_DIR", profiles)
    monkeypatch.setattr(config, "REVIEW_DIR", review)
    monkeypatch.setattr(config, "PUBLIC_DIR", public)
    monkeypatch.setattr(config, "FIXTURE_DIR", review / "fixtures")
    monkeypatch.setattr(config, "RECEIPT_DIR", review / "receipts")
    monkeypatch.setattr(config, "DECISION_DIR", review / "decisions")
    monkeypatch.setattr(config, "UPLOAD_DIR", review / "uploads")
    monkeypatch.setattr(config, "OVERRIDE_DIR", review / "overrides")
    monkeypatch.setattr(config, "QUARANTINE_DIR", review / "quarantine")
    monkeypatch.setattr(config, "CASES_FILE", review / "cases.json")
    monkeypatch.setattr(config, "JUSTIFICATION_FILE", review / "justifications.json")
    monkeypatch.setattr(config, "MANIFEST_FILE", data / "manifest.json")
    monkeypatch.setattr(config, "SOURCES_FILE", data / "sources.json")

    config.ensure_runtime_dirs()

    for directory in (
        data,
        profiles,
        review,
        public,
        review / "uploads",
        review / "receipts",
        review / "decisions",
        public / "aggregates",
        public / "receipts",
    ):
        assert directory.is_dir()
    assert json.loads((review / "cases.json").read_text())["cases"] == []
    assert (
        json.loads((review / "justifications.json").read_text())["justifications"] == {}
    )
    assert json.loads((data / "manifest.json").read_text())["items"] == []

    sentinel = {"uploads": {"kept": {"id": "kept"}}}
    (review / "uploads" / "manifest.json").write_text(json.dumps(sentinel))
    config.ensure_runtime_dirs()
    assert json.loads((review / "uploads" / "manifest.json").read_text()) == sentinel


def test_api_startup_recreates_missing_runtime_folders(sandbox):
    from engine.api import app

    shutil.rmtree(config.UPLOAD_DIR, ignore_errors=True)
    shutil.rmtree(config.PUBLIC_DIR / "aggregates", ignore_errors=True)
    with TestClient(app):
        pass
    assert config.UPLOAD_DIR.is_dir()
    assert (config.PUBLIC_DIR / "aggregates").is_dir()
