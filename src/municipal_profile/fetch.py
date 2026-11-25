"""Download, cache and fingerprint the official INE spreadsheets.

The pipeline is offline-first: a local file is used when present. Missing files
are fetched from the exact official URL in :mod:`municipal_profile.catalog`,
written atomically and recorded with a UTC timestamp and SHA-256 digest.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import httpx

from .catalog import SOURCES, Source

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_PROVENANCE_PATH = PROJECT_ROOT / "data" / "provenance.json"

USER_AGENT = "MunicipalDemandProfile/0.1 (Dataton INE 2026; local research pipeline)"
CHUNK = 1024 * 256


def utc_now() -> str:
    return (
        datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    )


def utc_from_timestamp(ts: float) -> str:
    return (
        datetime.fromtimestamp(ts, tz=timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def download_to(url: str, destination: Path, timeout: float = 600.0) -> int:
    """Stream ``url`` to ``destination`` with retries; return bytes written.

    The INE data bank occasionally stalls on large DINESE files, so each
    attempt is retried from scratch on transport errors and 5xx responses.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    attempts = 3
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        destination.unlink(missing_ok=True)
        written = 0
        try:
            with httpx.stream(
                "GET",
                url,
                follow_redirects=True,
                timeout=httpx.Timeout(
                    timeout, connect=30.0, read=timeout, write=60.0, pool=30.0
                ),
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "application/octet-stream",
                },
            ) as response:
                if response.status_code in {429, 500, 502, 503, 504}:
                    raise httpx.HTTPStatusError(
                        f"HTTP {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                response.raise_for_status()
                with destination.open("wb") as handle:
                    for chunk in response.iter_bytes(CHUNK):
                        if chunk:
                            handle.write(chunk)
                            written += len(chunk)
            if written == 0:
                raise RuntimeError(f"La descarga de {url} quedó vacía")
            return written
        except (
            httpx.TimeoutException,
            httpx.TransportError,
            httpx.HTTPStatusError,
        ) as exc:
            last_error = exc
            destination.unlink(missing_ok=True)
            if attempt < attempts:
                print(
                    f"  reintentando descarga ({attempt}/{attempts - 1}): "
                    f"{type(exc).__name__}"
                )
                time.sleep(2 * attempt)

    raise RuntimeError(f"No se pudo descargar {url}: {last_error}") from last_error


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # corrupted cache should be explicit
        raise RuntimeError(f"No se pudo leer {path}: {exc}") from exc


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    )
    try:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
        handle.close()
        os.replace(handle.name, path)
    finally:
        if not handle.closed:
            handle.close()
        if Path(handle.name).exists():
            Path(handle.name).unlink(missing_ok=True)


def _validate_xlsx(path: Path) -> None:
    with path.open("rb") as handle:
        magic = handle.read(2)
    if magic != b"PK":
        raise RuntimeError(
            f"{path.name} no es un archivo XLSX válido (¿el servidor devolvió HTML?). "
            "Se eliminó el archivo parcial."
        )


def ensure_sources(
    raw_dir: Path | str = DEFAULT_RAW_DIR,
    provenance_path: Path | str = DEFAULT_PROVENANCE_PATH,
    sources: tuple[Source, ...] = SOURCES,
    *,
    force: bool = False,
    download: Callable[[str, Path], int] = download_to,
) -> dict:
    """Ensure every source exists locally and return the provenance snapshot.

    ``download`` is injectable so tests can exercise the missing-file path
    without touching the network.
    """
    raw_dir = Path(raw_dir)
    provenance_path = Path(provenance_path)
    raw_dir.mkdir(parents=True, exist_ok=True)

    previous = _read_json(provenance_path)
    previous_by_key = {item["key"]: item for item in previous.get("files", [])}
    downloads: list[dict] = list(previous.get("downloads", []))
    files: list[dict] = []

    for source in sources:
        path = raw_dir / source.filename
        entry = source.manifest_entry()

        if path.exists() and not force:
            digest = sha256_file(path)
            old = previous_by_key.get(source.key)
            if old and old.get("sha256") == digest and old.get("downloaded_at_utc"):
                downloaded_at = old["downloaded_at_utc"]
                timestamp_source = old.get("timestamp_source", "download_log")
            else:
                downloaded_at = utc_from_timestamp(path.stat().st_mtime)
                timestamp_source = "file_mtime"
            entry.update(
                {
                    "bytes": path.stat().st_size,
                    "sha256": digest,
                    "status": "cached",
                    "downloaded_at_utc": downloaded_at,
                    "last_verified_utc": utc_now(),
                    "timestamp_source": timestamp_source,
                }
            )
            files.append(entry)
            continue

        tmp_path = path.with_name(f".{path.name}.part")
        tmp_path.unlink(missing_ok=True)
        try:
            byte_count = download(source.url, tmp_path)
            _validate_xlsx(tmp_path)
            digest = sha256_file(tmp_path)
            os.replace(tmp_path, path)
        except Exception:
            tmp_path.unlink(missing_ok=True)
            raise

        downloaded_at = utc_now()
        actual_bytes = path.stat().st_size
        if byte_count != actual_bytes:
            byte_count = actual_bytes

        entry.update(
            {
                "bytes": byte_count,
                "sha256": digest,
                "status": "downloaded",
                "downloaded_at_utc": downloaded_at,
                "last_verified_utc": downloaded_at,
                "timestamp_source": "download_log",
            }
        )
        files.append(entry)
        downloads.append(
            {
                "key": source.key,
                "url": source.url,
                "downloaded_at_utc": downloaded_at,
                "sha256": digest,
                "bytes": byte_count,
                "filename": source.filename,
            }
        )
        print(f"  descargado {source.filename} ({byte_count:,} bytes)")

    payload = {
        "schema_version": 1,
        "generated_at_utc": utc_now(),
        "ine_data_bank": "https://datos.ine.gob.gt",
        "license_status": "Abierta — CKAN CC BY (Creative Commons Attribution)",
        "files": files,
        "downloads": downloads,
        "notes": [
            "Los archivos existentes se reutilizan sin red; solo se descargan los ausentes.",
            "Cada descarga registra URL exacta, fecha UTC y SHA-256.",
            "Si el archivo local no tiene registro previo, la fecha proviene del mtime del archivo.",
        ],
    }
    _atomic_write_json(provenance_path, payload)
    return payload


def load_provenance(path: Path | str = DEFAULT_PROVENANCE_PATH) -> dict:
    return _read_json(Path(path))


def verify_hashes(
    raw_dir: Path | str, provenance: dict, sources: tuple[Source, ...] = SOURCES
) -> dict[str, str]:
    """Verify cached inputs against the provenance manifest.

    Returns the current digests. Raises if a file is missing or its digest no
    longer matches the recorded one, so a build can never silently mix files.
    """
    raw_dir = Path(raw_dir)
    recorded = {item["key"]: item for item in provenance.get("files", [])}
    digests: dict[str, str] = {}
    for source in sources:
        path = raw_dir / source.filename
        if not path.exists():
            raise FileNotFoundError(
                f"Falta {path}. Ejecuta `uv run municipal-profile fetch` primero."
            )
        digest = sha256_file(path)
        expected = recorded.get(source.key, {}).get("sha256")
        if expected and expected != digest:
            raise RuntimeError(
                f"El SHA-256 de {path.name} no coincide con el manifiesto. "
                "Vuelve a descargarlo con `uv run municipal-profile fetch --force`."
            )
        digests[source.key] = digest
    return digests
