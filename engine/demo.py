#!/usr/bin/env python3
"""Prepare the demo offline: snapshot, validation, gate and verification.

It does not start the servers: that is `pnpm run dev`.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys

from . import config

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
    subprocess.run([sys.executable, *args], cwd=config.ROOT, check=True)


def reset() -> None:
    for directory in (
        config.RECEIPT_DIR,
        config.QUARANTINE_DIR,
        config.UPLOAD_DIR,
        config.OVERRIDE_DIR,
        config.PUBLIC_DIR / "aggregates",
        config.PUBLIC_DIR / "receipts",
    ):
        if directory.exists():
            shutil.rmtree(directory)
    for path in (config.DECISIONS_FILE, config.PUBLIC_DIR / "index.json"):
        if path.exists():
            path.unlink()
    _recreate_justifications()


def _recreate_justifications() -> None:
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
    config.JUSTIFICATION_FILE.write_text(
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

    run("-m", "engine.prepare", "--offline")
    run("-m", "engine.cli", "validate")
    for case_id, operator, rationale in PROMOTIONS:
        run(
            "-m",
            "engine.cli",
            "promote",
            case_id,
            "--operator",
            operator,
            "--rationale",
            rationale,
        )
    run("-m", "engine.cli", "verify")
    print("")
    print("Listo. Arranque la demo con: pnpm run demo:offline")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
