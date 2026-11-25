"""Local-first retrieval of the official INE spreadsheets.

A file is used when it already exists in ``data/raw`` (or ``data/reference``).
Only a missing (or corrupt) file triggers a download from the URL recorded in
:mod:`radar.config`. Every file that is downloaded is logged with its exact
URL, UTC timestamp and SHA-256 digest in a provenance manifest.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Callable, Iterable

from .config import Source

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0 Safari/537.36 radar-territorial-gt/0.1"
)

Downloader = Callable[[str, Path], None]


class SourceError(RuntimeError):
    """Raised when a required source is missing and cannot be downloaded."""


def utc_now() -> str:
    """Return a second-precision ISO-8601 UTC timestamp."""

    return (
        datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_valid(path: Path, kind: str) -> bool:
    """Cheap integrity check used before trusting a cached file."""

    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        if kind == "xlsx":
            if not zipfile.is_zipfile(path):
                return False
            with zipfile.ZipFile(path) as archive:
                names = archive.namelist()
                return any(name.endswith("workbook.xml") for name in names)
        if kind == "geojson":
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            return payload.get("type") == "FeatureCollection" and bool(
                payload.get("features")
            )
    except (OSError, ValueError, zipfile.BadZipFile):
        return False
    return path.stat().st_size > 0


def _default_downloader(url: str, destination: Path) -> None:
    """Download ``url`` with a cookie jar and one retry loop.

    The INE CKAN endpoint returns a small HTML challenge for HEAD requests but
    serves the real file to a normal GET with cookies, hence the opener.
    """

    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(CookieJar())
    )
    opener.addheaders = [("User-Agent", USER_AGENT), ("Accept", "*/*")]
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with (
                opener.open(request, timeout=180) as response,
                destination.open("wb") as out,
            ):
                shutil.copyfileobj(response, out, length=1024 * 1024)
            return
        except (
            urllib.error.URLError,
            TimeoutError,
            OSError,
        ) as exc:  # pragma: no cover - network
            last_error = exc
            if destination.exists():
                destination.unlink()
            if attempt < 3:
                time.sleep(1.5 * attempt)
    raise SourceError(f"No se pudo descargar {url}: {last_error}") from last_error


def _mtime_utc(path: Path) -> str:
    return (
        datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def ensure_sources(
    sources: Iterable[Source],
    destination: Path,
    manifest_path: Path,
    *,
    allow_network: bool = True,
    downloader: Downloader | None = None,
    now: str | None = None,
) -> list[dict]:
    """Make sure every source is present locally and return its manifest rows.

    Parameters are explicit so the fallback can be unit-tested without touching
    the network or the real data directory.
    """

    destination.mkdir(parents=True, exist_ok=True)
    downloader = downloader or _default_downloader
    now = now or utc_now()

    previous: dict[str, dict] = {}
    if manifest_path.exists():
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            previous = {row["filename"]: row for row in payload.get("sources", [])}
        except (OSError, ValueError, KeyError):
            previous = {}

    rows: list[dict] = []
    for source in sources:
        target = destination / source.filename
        status = "cached"
        retrieved_at = previous.get(source.filename, {}).get("retrieved_at_utc")
        origin = previous.get(source.filename, {}).get("origin", "local-cache")

        if not is_valid(target, source.kind):
            if not allow_network:
                raise SourceError(
                    f"Falta {source.filename} en {destination} y la ejecución es offline."
                )
            part = target.with_suffix(target.suffix + ".part")
            if part.exists():
                part.unlink()
            downloader(source.url, part)
            if not is_valid(part, source.kind):
                part.unlink(missing_ok=True)
                raise SourceError(
                    f"El archivo descargado para {source.filename} no es un {source.kind} válido."
                )
            os.replace(part, target)
            status = "downloaded"
            retrieved_at = now
            origin = "download"

        if not retrieved_at:
            retrieved_at = _mtime_utc(target)

        rows.append(
            {
                "filename": source.filename,
                "url": source.url,
                "kind": source.kind,
                "status": status,
                "origin": origin,
                "retrieved_at_utc": retrieved_at,
                "checked_at_utc": now,
                "sha256": sha256_file(target),
                "bytes": target.stat().st_size,
                "publisher": source.publisher,
                "license": source.license,
            }
        )

    manifest = {
        "generated_at_utc": now,
        "policy": (
            "Se usa el archivo local si existe y es válido; solo se descarga cuando falta "
            "o está corrupto. Cada descarga registra URL, fecha UTC y SHA-256."
        ),
        "sources": sorted(rows, key=lambda row: row["filename"]),
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(tmp, manifest_path)
    return manifest["sources"]


def load_manifest(path: Path) -> dict:
    if not path.exists():
        return {"sources": []}
    return json.loads(path.read_text(encoding="utf-8"))
