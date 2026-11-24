#!/usr/bin/env python3
"""Prepara el snapshot: descarga el recurso real, genera fixtures y escribe el
manifiesto con URL, fecha UTC, bytes, SHA-256 y perfil.

Este es el único paso que puede usar red. Después de preparar el snapshot, todo
el prototipo funciona offline.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from idt.canonical import file_sha256  # noqa: E402
from idt.config import DATA_DIR, FIXTURE_DIR  # noqa: E402
from idt.fixtures import write_fixtures  # noqa: E402

SOURCES_FILE = DATA_DIR / "sources.json"
MANIFEST_FILE = DATA_DIR / "manifest.json"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def download(url: str, target: Path) -> str:
    target.parent.mkdir(parents=True, exist_ok=True)
    print(f"descargando {url}")
    with urllib.request.urlopen(url, timeout=60) as response:
        data = response.read()
    target.write_bytes(data)
    print(f"  {len(data)} bytes -> {target}")
    return utc_now()


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
