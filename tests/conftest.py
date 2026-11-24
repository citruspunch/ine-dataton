from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from idt import config, gate  # noqa: E402

PROMOTIONS = ["ipc_empalme", "ipc_regional", "csv_ok", "dup_identidad_excepcion"]


@pytest.fixture()
def sandbox(tmp_path, monkeypatch):
    """Redirige todo lo escribible a un directorio temporal.

    Los datos de entrada (data/, profiles/, rules/, fixtures) siguen siendo los
    del repositorio: el test nunca modifica el snapshot real.
    """
    review = tmp_path / "review_store"
    public = tmp_path / "public_snapshot"
    review.mkdir()
    public.mkdir()

    monkeypatch.setattr(config, "REVIEW_DIR", review)
    monkeypatch.setattr(config, "PUBLIC_DIR", public)
    monkeypatch.setattr(config, "RECEIPT_DIR", review / "receipts")
    monkeypatch.setattr(config, "DECISION_DIR", review / "decisions")
    monkeypatch.setattr(config, "UPLOAD_DIR", review / "uploads")
    monkeypatch.setattr(config, "OVERRIDE_DIR", review / "overrides")
    monkeypatch.setattr(config, "QUARANTINE_DIR", review / "quarantine")
    monkeypatch.setattr(
        config, "DECISIONS_FILE", review / "decisions" / "decisions.jsonl"
    )
    monkeypatch.setattr(config, "UPLOAD_REGISTRY", review / "uploads" / "manifest.json")
    monkeypatch.setattr(config, "JUSTIFICATION_FILE", review / "justifications.json")

    source = ROOT / "review_store" / "justifications.json"
    target = review / "justifications.json"
    if source.exists():
        shutil.copyfile(source, target)
    else:
        target.write_text(
            json.dumps(
                {
                    "note": "Justificaciones de la suite de pruebas.",
                    "justifications": {
                        "dup_identidad_excepcion": {
                            "ID-01": {
                                "policy": "POL-DUP-TEST",
                                "owner": "Revisor de publicaciones (prueba)",
                                "date": "2026-11-24",
                                "reason": "Reutilización intencional documentada.",
                            }
                        }
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    return tmp_path


@pytest.fixture()
def seeded(sandbox):
    """Sandbox con los cuatro casos habilitados, como en la demo."""
    for case_id in PROMOTIONS:
        gate.promote(
            case_id,
            "Técnico de publicaciones (prueba)",
            "Aprobación registrada por la suite de pruebas.",
        )
    return sandbox


@pytest.fixture()
def client(seeded):
    from fastapi.testclient import TestClient

    from idt.web.app import app

    return TestClient(app)


@pytest.fixture()
def raw_client(sandbox):
    from fastapi.testclient import TestClient

    from idt.web.app import app

    return TestClient(app)


def reload_index(path: Path) -> list[str]:
    data = json.loads(
        (path / "public_snapshot" / "index.json").read_text(encoding="utf-8")
    )
    return sorted(a["case_id"] for a in data["aggregates"])
