"""Registry of files uploaded during the review session.

An uploaded file is not in the closed-list manifest, so on receipt it gets its
own manifest entry (bytes, SHA-256, UTC date). That way SNAP-01 keeps meaning
the same thing and still detects a later change to the file.
"""

from __future__ import annotations

import datetime as dt
import re
import shutil
from pathlib import Path
from typing import Any

from . import config
from .canonical import file_sha256

MAX_BYTES = 20 * 1024 * 1024
ALLOWED_SUFFIXES = {".csv", ".xlsx", ".xls"}

LICENSE_CHOICES = {
    "cc-by": {
        "id": "cc-by",
        "verified": True,
        "attribution": "Instituto Nacional de Estadística (INE), Guatemala",
        "evidence": "Licencia declarada por el revisor al cargar el archivo.",
        "synthetic": False,
    },
    "interno-fixture": {
        "id": "interno-fixture",
        "verified": True,
        "attribution": "Fixture sintético del equipo. No es un dato oficial del INE.",
        "evidence": "Fixture sintético generado por el equipo para pruebas.",
        "synthetic": True,
    },
    "sin-licencia": {
        "id": None,
        "verified": False,
        "attribution": None,
        "evidence": "El revisor no pudo verificar una licencia para este archivo.",
        "synthetic": False,
    },
}


class UploadError(Exception):
    pass


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _slug(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", text).strip("-")
    return cleaned[:60] or "file"


def _registry() -> dict[str, Any]:
    if config.UPLOAD_REGISTRY.exists():
        return config.load_json(config.UPLOAD_REGISTRY)
    return {"uploads": {}}


def list_uploads() -> list[dict[str, Any]]:
    data = _registry()
    return sorted(
        data.get("uploads", {}).values(),
        key=lambda entry: entry.get("uploaded_at_utc") or "",
        reverse=True,
    )


def get_upload(upload_id: str) -> dict[str, Any] | None:
    return _registry().get("uploads", {}).get(upload_id)


def register_upload(
    filename: str,
    content: bytes,
    profile_id: str,
    license_key: str = "cc-by",
    label: str | None = None,
) -> dict[str, Any]:
    if not content:
        raise UploadError("el archivo está vacío")
    if len(content) > MAX_BYTES:
        raise UploadError("el archivo supera el límite de 20 MB")

    name = Path(filename or "archivo").name
    suffix = Path(name).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise UploadError(
            f"extensión no aceptada: {suffix or 'sin extensión'}. "
            "Use .csv, .xlsx o .xls"
        )
    if license_key not in LICENSE_CHOICES:
        raise UploadError(f"licencia desconocida: {license_key}")

    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    temp = config.UPLOAD_DIR / f".incoming-{_slug(name)}"
    temp.write_bytes(content)
    digest_hex = file_sha256(temp)

    upload_id = f"up-{_slug(profile_id)}-{digest_hex[:8]}"
    target = config.UPLOAD_DIR / f"{upload_id}{suffix}"
    if target.exists():
        target.unlink()
    shutil.move(str(temp), str(target))

    license_info = LICENSE_CHOICES[license_key]
    try:
        stored_path = str(target.relative_to(config.ROOT))
    except ValueError:
        stored_path = str(target)
    item = {
        "id": upload_id,
        "kind": "upload",
        "synthetic": license_info.get("synthetic", False),
        "source_id": None,
        "dataset_id": None,
        "resource_id": None,
        "title": f"Archivo cargado: {name}",
        "path": stored_path,
        "source_url": None,
        "downloaded_at_utc": _utc_now(),
        "bytes": len(content),
        "sha256": digest_hex,
        "profile": profile_id,
        "origin": "upload",
        "license": {k: v for k, v in license_info.items() if k != "synthetic"},
    }
    entry = {
        "id": upload_id,
        "label": label or f"{name} · {profile_id}",
        "profile_id": profile_id,
        "original_name": name,
        "uploaded_at_utc": item["downloaded_at_utc"],
        "item": item,
    }

    data = _registry()
    data.setdefault("uploads", {})[upload_id] = entry
    config.dump_json(data, config.UPLOAD_REGISTRY)
    return entry


def delete_upload(upload_id: str) -> None:
    data = _registry()
    entry = data.get("uploads", {}).pop(upload_id, None)
    if not entry:
        return
    path = config.ROOT / entry["item"]["path"]
    if path.exists():
        path.unlink()
    config.dump_json(data, config.UPLOAD_REGISTRY)
