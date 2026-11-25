"""Command line entry point: ``uv run radar build``."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .build import build
from .config import (
    ALL_SOURCES,
    CORE_SOURCES,
    GEO_SOURCES,
    RAW_DIR,
    REFERENCE_DIR,
    WEB_DATA_DIR,
)
from .fetch import SourceError, ensure_sources, load_manifest, utc_now


def fetch_all(*, allow_network: bool = True) -> list[dict]:
    """Retrieve the official files into their local cache directories."""

    raw_rows = ensure_sources(
        CORE_SOURCES,
        RAW_DIR,
        RAW_DIR / "provenance.json",
        allow_network=allow_network,
    )
    reference_rows = ensure_sources(
        GEO_SOURCES,
        REFERENCE_DIR,
        REFERENCE_DIR / "provenance.json",
        allow_network=allow_network,
    )
    return raw_rows + reference_rows


def run_build(*, allow_network: bool = True) -> dict:
    provenance = fetch_all(allow_network=allow_network)
    result = build(RAW_DIR, REFERENCE_DIR, WEB_DATA_DIR, provenance)
    print(
        f"OK · {result['municipalities']} municipios · "
        f"{result['points']:,} puntos · salida {Path(result['outputDir']).relative_to(Path.cwd())}"
    )
    return result


def verify_outputs(web_dir: Path = WEB_DATA_DIR) -> dict:
    """Fail loudly if a privacy or geography invariant is broken."""

    territories = json.loads((web_dir / "territories.json").read_text(encoding="utf-8"))
    indicators = json.loads((web_dir / "indicators.json").read_text(encoding="utf-8"))
    meta = json.loads((web_dir / "meta.json").read_text(encoding="utf-8"))
    points = json.loads((web_dir / "points.json").read_text(encoding="utf-8"))

    assert len(territories["municipalities"]) == 340
    assert len(territories["departments"]) == 22
    assert meta["pointLayer"]["included"] == len(points["points"])
    assert meta["pointLayer"]["excluded_suffix_999"] == 301
    assert meta["pointLayer"]["excluded_missing_coordinates"] == 313

    def walk(node, path="root"):
        if isinstance(node, dict):
            if node.get("suppressed") is True:
                forbidden = {"count", "rate"} & set(node)
                assert not forbidden, f"Celda suprimida expone {forbidden} en {path}"
            else:
                for key, value in node.items():
                    walk(value, f"{path}.{key}")
        elif isinstance(node, list):
            for index, value in enumerate(node):
                walk(value, f"{path}[{index}]")

    walk(indicators)
    causes = json.loads((web_dir / "death-causes.json").read_text(encoding="utf-8"))
    walk(causes)
    ages = json.loads((web_dir / "age-profile.json").read_text(encoding="utf-8"))
    walk(ages)

    return {
        "municipalities": len(territories["municipalities"]),
        "departments": len(territories["departments"]),
        "points": len(points["points"]),
        "suppressed_cells_checked": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="radar",
        description="Pipeline del Radar territorial de seguridad vial y salud (Guatemala 2025).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    fetch_parser = sub.add_parser(
        "fetch", help="Descarga solo los archivos que falten."
    )
    fetch_parser.add_argument("--offline", action="store_true")

    build_parser = sub.add_parser(
        "build", help="Descarga lo faltante y construye los JSON."
    )
    build_parser.add_argument("--offline", action="store_true")

    verify_parser = sub.add_parser(
        "verify", help="Verifica los invariantes de privacidad y geografía."
    )
    verify_parser.add_argument("--data-dir", type=Path, default=WEB_DATA_DIR)

    args = parser.parse_args(argv)
    try:
        if args.command == "fetch":
            rows = fetch_all(allow_network=not args.offline)
            print(f"OK · {len(rows)} fuentes locales verificadas.")
            for row in rows:
                print(
                    f"  {row['status']:>10}  {row['filename']}  {row['sha256'][:12]}…"
                )
        elif args.command == "build":
            run_build(allow_network=not args.offline)
        elif args.command == "verify":
            result = verify_outputs(args.data_dir)
            print(
                f"OK · {result['municipalities']} municipios, {result['departments']} "
                f"departamentos, {result['points']:,} puntos, celdas suprimidas sin valores."
            )
    except (SourceError, AssertionError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
