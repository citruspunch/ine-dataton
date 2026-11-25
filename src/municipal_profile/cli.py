"""Command line entry point: ``uv run municipal-profile [fetch|build|all]``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .build import DEFAULT_OUT_DIR, build, build_all
from .fetch import (
    DEFAULT_PROVENANCE_PATH,
    DEFAULT_RAW_DIR,
    ensure_sources,
    load_provenance,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="municipal-profile",
        description=(
            "Construye el perfil municipal con Censo 2018 y DINESE 2021/2022/2024. "
            "Descarga solo los .xlsx ausentes desde el banco de datos del INE."
        ),
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=DEFAULT_RAW_DIR,
        help=f"carpeta de .xlsx (por defecto: {DEFAULT_RAW_DIR})",
    )
    parser.add_argument(
        "--provenance",
        type=Path,
        default=DEFAULT_PROVENANCE_PATH,
        help=f"manifiesto de descargas (por defecto: {DEFAULT_PROVENANCE_PATH})",
    )

    sub = parser.add_subparsers(dest="command")
    fetch = sub.add_parser("fetch", help="descargar/verificar los .xlsx del INE")
    fetch.add_argument("--force", action="store_true", help="volver a descargar todo")

    build_parser = sub.add_parser("build", help="generar los JSON agregados")
    build_parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help=f"salida JSON (por defecto: {DEFAULT_OUT_DIR})",
    )

    all_parser = sub.add_parser("all", help="fetch + build (recomendado)")
    all_parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help=f"salida JSON (por defecto: {DEFAULT_OUT_DIR})",
    )
    all_parser.add_argument(
        "--force", action="store_true", help="volver a descargar los .xlsx"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    command = args.command or "all"

    if command == "fetch":
        provenance = ensure_sources(
            raw_dir=args.raw_dir,
            provenance_path=args.provenance,
            force=args.force,
        )
        print(
            f"Procedencia: {len(provenance['files'])} archivos, "
            f"manifiesto en {args.provenance}"
        )
        return 0

    if command == "build":
        provenance = load_provenance(args.provenance)
        manifest = build(
            args.raw_dir,
            args.out_dir,
            provenance=provenance,
            provenance_path=args.provenance,
        )
        print(
            f"Listo: {len(manifest['outputs'])} JSON en {args.out_dir} "
            f"({manifest['counts']['municipalities']} municipios, "
            f"{manifest['counts']['places_map_points']:,} puntos de lugares poblados)"
        )
        return 0

    # all
    if args.force:
        provenance = ensure_sources(
            raw_dir=args.raw_dir,
            provenance_path=args.provenance,
            force=True,
        )
        manifest = build(
            args.raw_dir,
            args.out_dir,
            provenance=provenance,
            provenance_path=args.provenance,
        )
    else:
        manifest = build_all(
            args.raw_dir,
            args.out_dir,
            provenance_path=args.provenance,
        )
    print(
        f"Listo: {len(manifest['outputs'])} JSON en {args.out_dir} "
        f"({manifest['counts']['municipalities']} municipios, "
        f"{manifest['counts']['places_map_points']:,} puntos de lugares poblados)"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
