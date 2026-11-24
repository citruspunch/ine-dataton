#!/usr/bin/env python3
"""Prepara la demo sin red: snapshot, validación, gate y verificación.

No arranca el servidor: eso lo hace `make demo` o `python app.py`.
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
        "Ficha oficial cotejada: la variación publicada en G504 coincide con la "
        "calculada desde F503 y F504; el cruce entre bases queda bloqueado.",
    ),
    (
        "ipc_regional",
        "Técnico de publicaciones (prototipo)",
        "Segundo recurso real evaluado con un perfil distinto sin tocar el motor. "
        "Publica índices por región; no publica variación mensual.",
    ),
    (
        "csv_ok",
        "Técnico de publicaciones (prototipo)",
        "Contrato sintético correcto; se usa para demostrar el flujo de habilitación.",
    ),
    (
        "dup_identidad_excepcion",
        "Revisor de publicaciones (prototipo)",
        "POL-DUP-2026-01 aplicada: reutilización intencional del mismo archivo, "
        "documentada con dueño, fecha y motivo.",
    ),
]


def run(*args: str) -> None:
    print(f"\n$ {' '.join(args)}", flush=True)
    subprocess.run([PY, *args], cwd=ROOT, check=True)


def reset() -> None:
    for directory in (
        ROOT / "review_store" / "receipts",
        ROOT / "review_store" / "quarantine",
        ROOT / "review_store" / "uploads",
        ROOT / "review_store" / "overrides",
        ROOT / "public_snapshot" / "aggregates",
        ROOT / "public_snapshot" / "receipts",
    ):
        if directory.exists():
            shutil.rmtree(directory)
    decisions = ROOT / "review_store" / "decisions" / "decisions.jsonl"
    if decisions.exists():
        decisions.unlink()
    index = ROOT / "public_snapshot" / "index.json"
    if index.exists():
        index.unlink()
    justifications = ROOT / "review_store" / "justifications.json"
    if justifications.exists():
        justifications.unlink()
    _recreate_justifications()


def _recreate_justifications() -> None:
    import json

    data = {
        "note": (
            "Justificaciones documentadas de advertencias. Una advertencia sin dueño, "
            "fecha y motivo deja el caso en revisión; no habilita."
        ),
        "justifications": {
            "dup_identidad_excepcion": {
                "ID-01": {
                    "policy": "POL-DUP-2026-01",
                    "owner": "Revisor de publicaciones (rol del prototipo)",
                    "date": "2026-11-24",
                    "reason": (
                        "El mismo archivo se reutiliza de forma intencional como "
                        "plantilla de dos series de eventos vitales. La reutilización "
                        "no se publica y queda sujeta al gate humano."
                    ),
                    "gate": "requiere visto bueno humano registrado en la bitácora local",
                }
            }
        },
    }
    path = ROOT / "review_store" / "justifications.json"
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--reset",
        action="store_true",
        help="borra recibos, decisiones, cargas y snapshot público antes de correr",
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
    run("-m", "idt", "verify")
    print("")
    print("Listo. Arranque la interfaz con: make serve   (o python app.py)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
