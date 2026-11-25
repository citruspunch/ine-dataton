"""CLI de ingesta: ``uv run basket-ingest``.

Flujo:
1. Verifica los siete archivos requeridos en ``data/raw``.
2. Descarga los faltantes del portal CKAN del INE y registra URL, fecha UTC y SHA-256.
3. Normaliza meses, cálculos y empalme del IPC.
4. Escribe Parquet en ``data/processed``, un manifiesto y el JSON que lee Next.js.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .build import build_pipeline
from .download import utc_now_iso
from .errors import IngestError
from .export import write_outputs


def _repo_root() -> Path:
    # pipeline/src/ine_basket/cli.py -> raíz del repositorio
    return Path(__file__).resolve().parents[3]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="basket-ingest",
        description=(
            "Normaliza la CBA urbana/rural y el IPC del INE Guatemala, aplica el "
            "empalme oficial y genera Parquet + JSON para el simulador."
        ),
    )
    parser.add_argument("--raw-dir", type=Path, default=None, help="Carpeta de .xls/.xlsx")
    parser.add_argument(
        "--processed-dir", type=Path, default=None, help="Salida de Parquet y manifiesto"
    )
    parser.add_argument(
        "--web-data-dir", type=Path, default=None, help="Salida del JSON para Next.js"
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Vuelve a descargar los archivos aunque existan localmente",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="No usa la red: falla si falta algún archivo local",
    )
    parser.add_argument("--quiet", action="store_true", help="Sólo imprime errores")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = _repo_root()
    raw_dir = (args.raw_dir or repo_root / "data" / "raw").resolve()
    processed_dir = (args.processed_dir or repo_root / "data" / "processed").resolve()
    web_data_dir = (args.web_data_dir or repo_root / "web" / "src" / "data").resolve()

    log = (lambda *_: None) if args.quiet else print
    log("──────────────────────────────────────────────────────────────")
    log(" CBA + IPC · Ingesta INE Guatemala")
    log(f" Datos crudos : {raw_dir}")
    log(f" Parquet      : {processed_dir}")
    log(f" JSON web     : {web_data_dir / 'basket.json'}")
    log("──────────────────────────────────────────────────────────────")

    try:
        result = build_pipeline(
            repo_root=repo_root,
            raw_dir=raw_dir,
            refresh=args.refresh,
            offline=args.offline,
            clock=utc_now_iso,
        )
        exported = write_outputs(
            result,
            processed_dir=processed_dir,
            web_data_dir=web_data_dir,
        )
    except IngestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    manifest = exported["manifest"]
    log("")
    log("Fuentes")
    for source in manifest["sources"]:
        origin = {
            "download": "descargado ahora",
            "local-cache": "caché local verificada",
            "local-file": "archivo local (sin registro de descarga)",
        }[source["retrieved_from"]]
        stamp = source["downloaded_at_utc"] or "—"
        log(f"  • {source['filename']:<42} {origin:<14} {stamp}")
        log(f"    sha256 {source['sha256'][:16]}…  licencia: {source['license']['status']}")

    log("")
    log("Tablas")
    for output in manifest["outputs"]:
        log(
            f"  • {output['file']:<28} {output['rows']:>5} filas  {output['bytes'] / 1024:7.1f} KiB"
        )

    log("")
    periods = manifest["periods"]
    log(f"Periodos: {periods['count']} ({periods['first']} a {periods['last']})")
    for area, check in manifest["checks"].items():
        log(
            f"  {area}: {check['products']} productos · {check['groups']} grupos · "
            f"{check['kcalPerDay']:.0f} kcal/día · brecha máxima por grupo "
            f"Q{check['maxGroupCostGapQ']:.3f}"
        )
    rules = manifest["rules"]
    log("")
    log(
        f"Empalme IPC: enero 2025 oficial {rules['official_jan_2025_monthly_var_pct']:+.4f} % "
        f"vs. directo {rules['direct_jan_2025_monthly_var_pct']:+.4f} % "
        f"(factor {rules['link_factor_2023_to_2024']:.6f})"
    )
    log(f"Manifiesto: {processed_dir / 'manifest.json'}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
