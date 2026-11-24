"""Rutas del repositorio y carga de la configuración declarativa."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PROFILE_DIR = ROOT / "profiles"
RULE_DIR = ROOT / "rules"
REVIEW_DIR = ROOT / "review_store"
PUBLIC_DIR = ROOT / "public_snapshot"

FIXTURE_DIR = REVIEW_DIR / "fixtures"
RECEIPT_DIR = REVIEW_DIR / "receipts"
DECISION_DIR = REVIEW_DIR / "decisions"
REVIEW_SITE_DIR = REVIEW_DIR / "site"

CASES_FILE = REVIEW_DIR / "cases.json"
JUSTIFICATION_FILE = REVIEW_DIR / "justifications.json"
MANIFEST_FILE = DATA_DIR / "manifest.json"
DECISIONS_FILE = DECISION_DIR / "decisions.jsonl"


class ConfigError(Exception):
    pass


def load_json(path: Path) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError as exc:
        raise ConfigError(f"falta {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"JSON inválido en {path.relative_to(ROOT)}: {exc}") from exc


def load_manifest() -> dict[str, Any]:
    return load_json(MANIFEST_FILE)


def manifest_item(item_id: str) -> dict[str, Any]:
    for item in load_manifest()["items"]:
        if item["id"] == item_id:
            return item
    raise ConfigError(f"ítem de manifiesto desconocido: {item_id}")


def load_cases() -> list[dict[str, Any]]:
    return load_json(CASES_FILE)["cases"]


def load_case(case_id: str) -> dict[str, Any]:
    for case in load_cases():
        if case["id"] == case_id:
            return case
    raise ConfigError(f"caso desconocido en la lista cerrada: {case_id}")


def load_profile(profile_id: str) -> dict[str, Any]:
    path = PROFILE_DIR / f"{profile_id}.json"
    profile = load_json(path)
    for key in ("profile_id", "version", "kind"):
        if key not in profile:
            raise ConfigError(f"perfil {profile_id} sin campo {key}")
    return profile


def load_rules() -> dict[str, Any]:
    return load_json(RULE_DIR / "rules.json")


def rule_meta(rules_doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {rule["id"]: rule for rule in rules_doc["rules"]}


def load_justifications() -> dict[str, Any]:
    return load_json(JUSTIFICATION_FILE)


def justification_for(case_id: str, rule_id: str) -> dict[str, Any] | None:
    entry = load_justifications().get("justifications", {}).get(case_id, {})
    return entry.get(rule_id)


def load_decisions() -> list[dict[str, Any]]:
    if not DECISIONS_FILE.exists():
        return []
    decisions = []
    with open(DECISIONS_FILE, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                decisions.append(json.loads(line))
    return decisions


def latest_decision(case_id: str) -> dict[str, Any] | None:
    current = None
    for decision in load_decisions():
        if decision.get("case_id") == case_id:
            current = decision
    return current
