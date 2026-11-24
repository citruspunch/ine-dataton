#!/usr/bin/env python3
"""Ejecuta la demo completa en un solo comando, sin red.

Prepara el snapshot desde los archivos locales, valida los ocho casos, registra
el gate humano de los tres casos habilitables, genera los dos sitios y verifica
que los digests de decisión siguen vigentes.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable

PROMOTIONS = [
    (
        "ipc_empalme",
        "Técnico de publicaciones (prototipo)",
        "Ficha oficial cotejada: la variación publicada en G504 coincide con la calculada desde F503 y F504; la comparación entre bases queda bloqueada.",
    ),
    (
        "csv_ok",
        "Técnico de publicaciones (prototipo)",
        "Contrato sintético correcto; se usa para demostrar el flujo de habilitación.",
    ),
    (
        "dup_identidad_excepcion",
        "Revisor de publicaciones (prototipo)",
        "POL-DUP-2026-01 aplicada: reutilización intencional del mismo archivo, documentada con dueño, fecha y motivo.",
    ),
]


def run(*args: str) -> None:
    print(f"\n$ {' '.join(args)}", flush=True)
    subprocess.run([PY, *args], cwd=ROOT, check=True)


def reset() -> None:
    for directory in (
        ROOT / "review_store" / "receipts",
        ROOT / "review_store" / "quarantine",
        ROOT / "public_snapshot" / "aggregates",
        ROOT / "public_snapshot" / "site",
        ROOT / "review_store" / "site",
    ):
        if directory.exists():
            shutil.rmtree(directory)
    decisions = ROOT / "review_store" / "decisions" / "decisions.jsonl"
    if decisions.exists():
        decisions.unlink()
    index = ROOT / "public_snapshot" / "index.json"
    if index.exists():
        index.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reset",
        action="store_true",
        help="borra recibos, decisiones y snapshot público antes de correr",
    )
    args = parser.parse_args()

    if args.reset:
        reset()

    run("tools/prepare_snapshot.py", "--offline")
    run("-m", "idt", "validate")
    for case_id, operator, rationale in PROMOTIONS:
        run(
            "-m",
            "idt",
            "promote",
            case_id,
            "--operator",
            operator,
            "--rationale",
            rationale,
        )
    run("-m", "idt", "site")
    run("-m", "idt", "verify")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
