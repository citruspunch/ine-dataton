"""Download/cache layer with a hash-and-timestamp manifest.

Rules implemented here:

* a file that already exists locally is never downloaded again;
* a missing file is fetched from the exact URL in ``pipeline.sources``;
* every file is recorded with URL, UTC timestamp, SHA-256 and byte count;
* downloads are written atomically and validated before being accepted;
* a file with a broken signature is rejected instead of poisoning the cache.

The fetcher is injectable so unit tests can prove the missing-file path without
touching the network.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import tempfile
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable
from urllib.parse import urlparse

import requests

try:  # use the operating system trust store (MINEDUC's chain is not in certifi)
    import truststore

    truststore.inject_into_ssl()
except Exception:  # pragma: no cover - optional hardening
    pass

from .sources import SOURCE_BY_ID, SOURCES, Source, VERIFIED_ON


MANIFEST_NAME = "manifest.json"
USER_AGENT = (
    "local-growth-pressure-monitor/0.1 "
    "(Dataton INE 2026; reproducible municipal comparison; contact: local team)"
)


class DownloadError(RuntimeError):
    """Raised when a required source cannot be cached locally."""


@dataclass(frozen=True)
class FetchResult:
    body: bytes
    http_status: int = 200
    content_type: str = "application/octet-stream"


Fetcher = Callable[[str], FetchResult | bytes]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(moment: datetime) -> str:
    return (
        moment.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def sha256_bytes(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def default_fetcher(url: str, timeout: int = 180) -> FetchResult:
    """Fetch a URL with a descriptive user agent and retries on transient errors."""

    last_error: Exception | None = None
    for attempt in range(6):
        try:
            response = requests.get(
                url,
                timeout=timeout,
                headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
                allow_redirects=True,
            )
            if response.status_code >= 400:
                raise DownloadError(
                    f"HTTP {response.status_code} for {url}: {response.text[:160]}"
                )
            return FetchResult(
                body=response.content,
                http_status=response.status_code,
                content_type=response.headers.get(
                    "content-type", "application/octet-stream"
                ),
            )
        except Exception as exc:  # network errors, timeouts, HTTP errors
            last_error = exc
            if attempt < 5:
                time.sleep(min(2**attempt, 10))
    raise DownloadError(f"No se pudo descargar {url}: {last_error}")


def _validate_bytes(source: Source, body: bytes) -> None:
    if len(body) < source.min_bytes:
        raise DownloadError(
            f"{source.id}: {len(body)} bytes es menor al mínimo esperado "
            f"({source.min_bytes}). Posible página de error o archivo truncado."
        )
    if source.expected_magic is not None and not body.startswith(source.expected_magic):
        raise DownloadError(
            f"{source.id}: firma inesperada; se esperaba {source.expected_magic!r}. "
            "El servidor probablemente devolvió HTML en lugar del archivo."
        )
    if source.format == "xlsx":
        if not zipfile.is_zipfile(io.BytesIO(body)):
            raise DownloadError(f"{source.id}: el archivo no es un XLSX válido (ZIP).")
    if source.format == "csv":
        head = body[:1024].lstrip()
        if head.lower().startswith((b"<html", b"<!doctype")):
            raise DownloadError(f"{source.id}: el CSV remoto es una página HTML.")


def _record(
    source: Source,
    *,
    path: Path,
    data_dir: Path,
    downloaded_at_utc: str,
    status: str,
    http_status: int | None,
    content_type: str | None,
) -> dict:
    relative = path.relative_to(data_dir).as_posix()
    return {
        "source_id": source.id,
        "title": source.title,
        "publisher": source.publisher,
        "dataset_page": source.dataset_page,
        "url": source.download_url,
        "filename": source.filename,
        "path": relative,
        "format": source.format,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "downloaded_at_utc": downloaded_at_utc,
        "last_seen_at_utc": iso_utc(utc_now()),
        "download_status": status,
        "http_status": http_status,
        "content_type": content_type,
        "license": source.license.as_dict(),
        "attribution": source.attribution,
        "description": source.description,
        "verified_on": VERIFIED_ON,
    }


def ensure_source(
    source: Source,
    data_dir: Path,
    previous: dict | None = None,
    *,
    fetcher: Fetcher | None = None,
    now: datetime | None = None,
) -> dict:
    """Return a manifest record for ``source``, downloading only if missing."""

    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / source.filename
    now = now or utc_now()

    # Reuse a locally supplied file that keeps the publisher's original name
    # (for example data/nacimientos_2025.xlsx) instead of forcing a re-download.
    if not path.exists():
        original_name = Path(urlparse(source.download_url).path).name
        original_path = data_dir / original_name
        if (
            original_name
            and original_name != source.filename
            and original_path.exists()
            and original_path.stat().st_size > 0
        ):
            shutil.copy2(original_path, path)

    if path.exists() and path.stat().st_size > 0:
        digest = sha256_file(path)
        if (
            previous
            and previous.get("sha256") == digest
            and previous.get("filename") == source.filename
        ):
            record = dict(previous)
            record.update(
                {
                    "path": path.relative_to(data_dir).as_posix(),
                    "bytes": path.stat().st_size,
                    "last_seen_at_utc": iso_utc(now),
                    "download_status": "cached",
                    "license": source.license.as_dict(),
                    "attribution": source.attribution,
                }
            )
            return record
        # A local copy without a matching manifest entry: be honest about it.
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        return _record(
            source,
            path=path,
            data_dir=data_dir,
            downloaded_at_utc=iso_utc(mtime),
            status="local_cache",
            http_status=None,
            content_type=None,
        )

    fetch = fetcher or default_fetcher
    result = fetch(source.download_url)
    if not isinstance(result, FetchResult):
        result = FetchResult(body=result)
    _validate_bytes(source, result.body)

    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{source.filename}.", suffix=".part", dir=data_dir
    )
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(result.body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)

    return _record(
        source,
        path=path,
        data_dir=data_dir,
        downloaded_at_utc=iso_utc(now),
        status="downloaded",
        http_status=result.http_status,
        content_type=result.content_type,
    )


def load_manifest(data_dir: Path) -> dict:
    path = Path(data_dir) / MANIFEST_NAME
    if not path.exists():
        return {"files": {}}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    data.setdefault("files", {})
    return data


def write_manifest(data_dir: Path, manifest: dict) -> Path:
    path = Path(data_dir) / MANIFEST_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(manifest)
    payload["generated_at_utc"] = iso_utc(utc_now())
    payload["verified_on"] = VERIFIED_ON
    fd, tmp_name = tempfile.mkstemp(
        prefix=".manifest.", suffix=".json", dir=path.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
    return path


def ensure_all(
    data_dir: Path,
    sources: Iterable[Source] = SOURCES,
    *,
    fetcher: Fetcher | None = None,
) -> dict:
    """Check every required file, download the missing ones, write the manifest."""

    data_dir = Path(data_dir)
    manifest = load_manifest(data_dir)
    files = manifest["files"]
    for source in sources:
        previous = files.get(source.id)
        files[source.id] = ensure_source(source, data_dir, previous, fetcher=fetcher)
        manifest["files"] = files
        write_manifest(data_dir, manifest)
    manifest["files"] = files
    write_manifest(data_dir, manifest)
    return manifest


def file_for(source_id: str, data_dir: Path) -> Path:
    source = SOURCE_BY_ID[source_id]
    path = Path(data_dir) / source.filename
    if not path.exists():
        raise DownloadError(
            f"Falta {path}. Ejecute `uv run build-pressure` para descargar la fuente."
        )
    return path
