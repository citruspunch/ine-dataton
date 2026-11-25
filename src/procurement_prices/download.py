"""Download missing INE files and record URL, UTC timestamp and SHA-256.

The checksum is computed over the exact bytes written to disk.  A 200 response
that is actually an HTML CAPTCHA page is rejected, so a broken mirror cannot
silently poison the cache.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests

from .config import RAW_DIR, ROOT, SourceSpec
from .provenance import (
    file_mtime_utc,
    load_manifest,
    save_manifest,
    sha256_bytes,
    sha256_file,
    utc_now,
)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0 Safari/537.36 municipal-procurement-prices/0.1"
)
TIMEOUT_SECONDS = 90


class DownloadError(RuntimeError):
    """Raised when no official URL yields a valid file."""


def _display_path(path: Path) -> str:
    """Prefer a repository-relative path in the portable provenance manifest."""

    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def validate_payload(payload: bytes, kind: str, filename: str) -> tuple[bool, str]:
    """Return ``(ok, reason)`` for a candidate download."""

    if len(payload) < 64:
        return False, "respuesta demasiado pequeña"
    head = payload[:400].lstrip().lower()
    if head.startswith(b"<!doctype html") or head.startswith(b"<html") or b"captcha" in head:
        return False, "la respuesta es HTML (posible CAPTCHA), no un archivo de datos"
    if kind == "xlsx":
        if not payload.startswith(b"PK\x03\x04"):
            return False, "el archivo no tiene la firma ZIP de un .xlsx"
        if len(payload) < 2_000:
            return False, "el .xlsx es sospechosamente pequeño"
        return True, "ok"
    if kind == "csv":
        try:
            text = payload[:4000].decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                text = payload[:4000].decode("latin-1")
            except UnicodeDecodeError:
                return False, "el CSV no se puede decodificar"
        if "<html" in text.lower() or "<!doctype" in text.lower():
            return False, "la respuesta es HTML, no un CSV"
        if "\n" not in text and ";" not in text and "," not in text:
            return False, "el CSV no tiene separadores reconocibles"
        return True, "ok"
    return True, "ok"


def _cached_entry(spec: SourceSpec, dest: Path, previous: dict[str, Any] | None) -> dict[str, Any]:
    entry = {
        "id": spec.id,
        "group": spec.group,
        "title": spec.title,
        "fileName": dest.name,
        "path": _display_path(dest),
        "sourcePage": spec.source_page,
        "publisher": spec.publisher,
        "license": {
            "id": spec.license_id,
            "title": spec.license_title,
            "url": spec.license_url,
        },
        "ckanModified": spec.ckan_modified,
        "retrieval": "local-cache",
        "url": (previous or {}).get("url"),
        "attemptedUrls": (previous or {}).get("attemptedUrls", []),
        "downloadedAtUtc": (previous or {}).get("downloadedAtUtc") or file_mtime_utc(dest),
        "verifiedAtUtc": utc_now(),
        "sha256": sha256_file(dest),
        "bytes": dest.stat().st_size,
        "httpStatus": (previous or {}).get("httpStatus"),
        "contentType": (previous or {}).get("contentType"),
    }
    return entry


def acquire_dataset(
    spec: SourceSpec,
    *,
    force: bool = False,
    dest: Path | None = None,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    """Ensure ``spec`` exists locally, downloading from an official URL if needed."""

    dest = Path(dest) if dest is not None else spec.path
    dest.parent.mkdir(parents=True, exist_ok=True)
    previous = load_manifest().get("datasets", {}).get(spec.id)

    if dest.exists() and not force:
        payload = dest.read_bytes()
        ok, _reason = validate_payload(payload, spec.kind, dest.name)
        if ok:
            return _cached_entry(spec, dest, previous)
        dest.unlink()

    http = session or requests.Session()
    attempted: list[dict[str, Any]] = []
    for url in spec.urls:
        try:
            response = http.get(
                url,
                timeout=TIMEOUT_SECONDS,
                headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
                allow_redirects=True,
            )
        except requests.RequestException as exc:  # pragma: no cover - network dependent
            attempted.append({"url": url, "error": f"{type(exc).__name__}: {exc}"})
            continue

        payload = response.content
        ok, reason = validate_payload(payload, spec.kind, dest.name)
        attempted.append(
            {
                "url": url,
                "status": response.status_code,
                "bytes": len(payload),
                "ok": ok and response.status_code == 200,
                "reason": reason if not ok else "ok",
            }
        )
        if response.status_code != 200 or not ok:
            continue

        tmp = dest.with_suffix(dest.suffix + ".part")
        tmp.write_bytes(payload)
        os.replace(tmp, dest)

        return {
            "id": spec.id,
            "group": spec.group,
            "title": spec.title,
            "fileName": dest.name,
            "path": _display_path(dest),
            "sourcePage": spec.source_page,
            "publisher": spec.publisher,
            "license": {
                "id": spec.license_id,
                "title": spec.license_title,
                "url": spec.license_url,
            },
            "ckanModified": spec.ckan_modified,
            "retrieval": "download",
            "url": url,
            "attemptedUrls": attempted,
            "downloadedAtUtc": utc_now(),
            "verifiedAtUtc": utc_now(),
            "sha256": sha256_bytes(payload),
            "bytes": len(payload),
            "httpStatus": response.status_code,
            "contentType": response.headers.get("content-type", ""),
        }

    detail = "; ".join(
        f"{item['url']} -> {item.get('error') or item.get('reason')}" for item in attempted
    )
    raise DownloadError(f"No se pudo obtener {spec.filename} desde las URLs oficiales. {detail}")


def acquire_all(
    specs: dict[str, SourceSpec],
    *,
    force: bool = False,
    dest_dir: Path | None = None,
) -> tuple[dict[str, Any], list[str]]:
    """Acquire every dataset, updating the provenance manifest.

    Returns the manifest and a list of human-readable errors.  Successful files
    are kept even if another file fails, which makes partial recovery possible.
    """

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    datasets: dict[str, Any] = manifest.get("datasets", {})
    errors: list[str] = []

    for spec in specs.values():
        dest = (dest_dir / spec.filename) if dest_dir is not None else spec.path
        try:
            entry = acquire_dataset(spec, force=force, dest=dest)
        except DownloadError as exc:
            errors.append(str(exc))
            continue
        datasets[spec.id] = entry
        print(
            f"  [{entry['retrieval']:>11}] {spec.filename} "
            f"{entry['bytes']:>9,} B  sha256:{entry['sha256'][:12]}…"
        )

    manifest["datasets"] = datasets
    manifest["generatedAt"] = utc_now()
    save_manifest(manifest)
    return manifest, errors
