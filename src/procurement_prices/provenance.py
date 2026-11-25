"""Hashing and UTC provenance helpers."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import DOWNLOADS_MANIFEST, PROVENANCE_DIR


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp with a trailing ``Z``."""

    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_manifest(path: Path = DOWNLOADS_MANIFEST) -> dict[str, Any]:
    if not path.exists():
        return {"generatedAt": None, "datasets": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"generatedAt": None, "datasets": {}}


def save_manifest(manifest: dict[str, Any], path: Path = DOWNLOADS_MANIFEST) -> None:
    PROVENANCE_DIR.mkdir(parents=True, exist_ok=True)
    manifest["generatedAt"] = utc_now()
    path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def file_mtime_utc(path: Path) -> str:
    return (
        datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
