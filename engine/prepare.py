#!/usr/bin/env python3
"""Prepare the snapshot: download the real resource, generate fixtures and write
the manifest with URL, UTC date, bytes, SHA-256 and profile.

This is the only step allowed to use the network. Once the snapshot is prepared,
the whole prototype works offline.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.request
from pathlib import Path

from .canonical import file_sha256
from .config import DATA_DIR, FIXTURE_DIR
from .fixtures import write_fixtures

SOURCES_FILE = DATA_DIR / "sources.json"
MANIFEST_FILE = DATA_DIR / "manifest.json"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def download(url: str, target: Path, attempts: int = 3) -> str:
    """Download with retries and a clear message. Returns the UTC date."""
    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"descargando {url}")
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                data = response.read()
            target.write_bytes(data)
            print(f"  {len(data)} bytes -> {target}")
            return utc_now()
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            print(f"  intento {attempt}/{attempts} falló: {exc}")
    raise SystemExit(
        f"no se pudo descargar {url}: {last_error}. "
        "Vuelva a intentarlo o use --offline si el archivo ya está en disco."
    )


def file_mtime_utc(path: Path) -> str:
    stamp = dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc)
    return stamp.strftime("%Y-%m-%dT%H:%M:%SZ")


def previous_items() -> dict[str, dict]:
    if not MANIFEST_FILE.exists():
        return {}
    try:
        with open(MANIFEST_FILE, "r", encoding="utf-8") as fh:
            return {item["id"]: item for item in json.load(fh)["items"]}
    except (json.JSONDecodeError, KeyError):
        return {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="no intenta descargar; falla si falta el archivo real",
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="vuelve a descargar aunque el archivo ya exista",
    )
    args = parser.parse_args()

    with open(SOURCES_FILE, "r", encoding="utf-8") as fh:
        sources = json.load(fh)

    print("generando fixtures sintéticos...")
    write_fixtures(FIXTURE_DIR)

    old = previous_items()
    items = []
    for spec in sources["items"]:
        path = Path(__file__).resolve().parent.parent / spec["path"]
        downloaded_at = None

        if spec["kind"] == "real":
            if not path.exists() or args.force_download:
                if args.offline:
                    print(
                        f"ERROR: falta {spec['path']} y se pidió --offline",
                        file=sys.stderr,
                    )
                    return 2
                downloaded_at = download(spec["source_url"], path)
            else:
                print(f"reutilizando {spec['path']}")

        actual_sha = file_sha256(path)
        size = path.stat().st_size

        if spec.get("expected_sha256") and actual_sha != spec["expected_sha256"]:
            print(
                f"ERROR: {spec['id']} no coincide con el SHA-256 esperado\n"
                f"  esperado {spec['expected_sha256']}\n"
                f"  observado {actual_sha}",
                file=sys.stderr,
            )
            return 3
        if spec.get("expected_bytes") and size != spec["expected_bytes"]:
            print(
                f"ERROR: {spec['id']} tiene {size} bytes, se esperaban {spec['expected_bytes']}",
                file=sys.stderr,
            )
            return 3

        if downloaded_at is None:
            prior = old.get(spec["id"])
            if prior and prior.get("sha256") == actual_sha:
                downloaded_at = prior.get("downloaded_at_utc")

        downloaded_source = "download"
        if downloaded_at is None:
            if spec["kind"] == "real" and path.exists():
                # The file was already on disk and the manifest did not record
                # the date: the UTC mtime is used and the source is declared.
                downloaded_at = file_mtime_utc(path)
                downloaded_source = "mtime"
            else:
                downloaded_source = "generado"

        item = {
            "id": spec["id"],
            "kind": spec["kind"],
            "synthetic": spec["kind"] == "synthetic",
            "source_id": spec.get("source_id"),
            "dataset_id": spec.get("dataset_id"),
            "resource_id": spec.get("resource_id"),
            "title": spec["title"],
            "path": spec["path"],
            "source_url": spec.get("source_url"),
            "downloaded_at_utc": downloaded_at,
            "downloaded_at_source": downloaded_source,
            "bytes": size,
            "sha256": actual_sha,
            "profile": spec.get("profile"),
            "license": spec["license"],
        }
        items.append(item)
        print(f"  {item['id']:34s} {size:>8d} B  {actual_sha[:16]}…")

    manifest = {
        "snapshot_id": sources["snapshot_id"],
        "prepared_at_utc": utc_now(),
        "note": sources["note"],
        "items": items,
    }
    with open(MANIFEST_FILE, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
        fh.write("\n")

    print(f"manifiesto escrito en {MANIFEST_FILE.relative_to(Path.cwd())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
