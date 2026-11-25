from __future__ import annotations

import json
from pathlib import Path

import pytest

from municipal_profile.build import build
from municipal_profile.fetch import PROJECT_ROOT, ensure_sources


@pytest.fixture(scope="session")
def artifacts(tmp_path_factory: pytest.TempPathFactory) -> dict:
    """Fetch (only if missing), build once, and return the generated artifacts."""
    raw_dir = PROJECT_ROOT / "data" / "raw"
    provenance_path = tmp_path_factory.mktemp("provenance") / "provenance.json"
    out_dir = tmp_path_factory.mktemp("output")

    provenance = ensure_sources(raw_dir=raw_dir, provenance_path=provenance_path)
    manifest = build(raw_dir, out_dir, provenance=provenance)

    meta = json.loads((out_dir / "meta.json").read_text(encoding="utf-8"))
    municipalities = json.loads(
        (out_dir / "municipalities.json").read_text(encoding="utf-8")
    )
    profiles = {
        path.stem: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((out_dir / "profiles").glob("*.json"))
    }
    return {
        "meta": meta,
        "municipalities": municipalities,
        "profiles": profiles,
        "manifest": manifest,
        "out_dir": out_dir,
        "raw_dir": raw_dir,
    }
