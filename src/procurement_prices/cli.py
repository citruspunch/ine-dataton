"""Command-line entry point: ``python -m procurement_prices``."""

from __future__ import annotations

import argparse
import sys

from .config import SOURCES
from .download import acquire_all
from .pipeline import build, verify


def _acquire(force: bool) -> int:
    print(f"Adquiriendo {len(SOURCES)} archivos oficiales del INE…")
    manifest, errors = acquire_all(SOURCES, force=force)
    print(f"Manifiesto: {len(manifest.get('datasets', {}))} conjuntos registrados.")
    if errors:
        print("\nErrores:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="procurement-prices",
        description=(
            "Ingesta, limpieza y procedencia de precios de referencia, índices de "
            "construcción y canastas básicas del INE Guatemala."
        ),
    )
    sub = parser.add_subparsers(dest="command")

    acquire_parser = sub.add_parser(
        "acquire", help="Descargar archivos faltantes y registrar procedencia"
    )
    acquire_parser.add_argument("--force", action="store_true", help="Volver a descargar todo")

    build_parser = sub.add_parser("build", help="Construir Parquet y JSON para la aplicación")
    build_parser.add_argument("--force", action="store_true", help="Volver a descargar todo")
    build_parser.add_argument("--offline", action="store_true", help="No usar la red")

    all_parser = sub.add_parser("all", help="Adquirir y construir")
    all_parser.add_argument("--force", action="store_true", help="Volver a descargar todo")
    all_parser.add_argument("--offline", action="store_true", help="No usar la red")

    sub.add_parser("verify", help="Verificar SHA-256 de los archivos cacheados")

    args = parser.parse_args(argv)

    if args.command == "acquire":
        return _acquire(args.force)
    if args.command == "build":
        build(force_download=args.force, offline=args.offline)
        return 0
    if args.command == "all":
        code = _acquire(args.force)
        if code != 0:
            return code
        build(force_download=False, offline=args.offline)
        return 0
    if args.command == "verify":
        problems = verify()
        if problems:
            print("Se encontraron problemas:", file=sys.stderr)
            for problem in problems:
                print(f"- {problem}", file=sys.stderr)
            return 1
        print("Todos los archivos coinciden con su SHA-256 registrado.")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
