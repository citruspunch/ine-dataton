"""Rutas del repositorio y carga de la configuración declarativa.

Los perfiles son YAML editables por una persona; los manifiestos y las
decisiones son JSON generados por el sistema.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PROFILE_DIR = ROOT / "profiles"
RULE_DIR = ROOT / "rules"
REVIEW_DIR = ROOT / "review_store"
PUBLIC_DIR = ROOT / "public_snapshot"

FIXTURE_DIR = REVIEW_DIR / "fixtures"
RECEIPT_DIR = REVIEW_DIR / "receipts"
DECISION_DIR = REVIEW_DIR / "decisions"
UPLOAD_DIR = REVIEW_DIR / "uploads"
OVERRIDE_DIR = REVIEW_DIR / "overrides"
QUARANTINE_DIR = REVIEW_DIR / "quarantine"

CASES_FILE = REVIEW_DIR / "cases.json"
JUSTIFICATION_FILE = REVIEW_DIR / "justifications.json"
MANIFEST_FILE = DATA_DIR / "manifest.json"
SOURCES_FILE = DATA_DIR / "sources.json"
DECISIONS_FILE = DECISION_DIR / "decisions.jsonl"
UPLOAD_REGISTRY = UPLOAD_DIR / "manifest.json"


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


def dump_json(obj: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")


# --------------------------------------------------------------------------
# Perfiles declarativos (YAML)
# --------------------------------------------------------------------------


def profile_path(profile_id: str) -> Path:
    return PROFILE_DIR / f"{profile_id}.yaml"


def read_yaml(path: Path) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    except FileNotFoundError as exc:
        raise ConfigError(f"falta {path.name}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML inválido en {path.name}: {exc}") from exc


def load_profile(profile_id: str, case_id: str | None = None) -> dict[str, Any]:
    """Carga el perfil declarativo.

    Si existe una enmienda de simulación para el caso, se aplica encima. Esa
    enmienda es la que permite demostrar la invalidación del digest en vivo.
    """
    if case_id:
        override = OVERRIDE_DIR / f"{case_id}.yaml"
        if override.exists():
            data = read_yaml(override)
            if isinstance(data, dict) and data.get("profile_id") == profile_id:
                _validate_profile(data, override.name)
                data["_override"] = True
                return data

    profile = read_yaml(profile_path(profile_id))
    if not isinstance(profile, dict):
        raise ConfigError(f"el perfil {profile_id} no es un mapa YAML")
    _validate_profile(profile, f"{profile_id}.yaml")
    return profile


def _validate_profile(profile: dict[str, Any], name: str) -> None:
    for key in ("profile_id", "version", "kind"):
        if key not in profile:
            raise ConfigError(f"perfil {name} sin campo {key}")
    if profile["kind"] not in ("xlsx", "delimited", "pair"):
        raise ConfigError(f"perfil {name}: kind desconocido {profile['kind']!r}")
    if profile["kind"] != "pair":
        if not profile.get("columns"):
            raise ConfigError(f"perfil {name} sin columnas")
        if not profile.get("grain"):
            raise ConfigError(f"perfil {name} sin grano")


def list_profiles() -> list[dict[str, Any]]:
    """Perfiles utilizables para cargar un archivo. Los del IPC van primero."""
    kind_label = {"delimited": "CSV", "xlsx": "XLSX"}
    out = []
    for path in sorted(PROFILE_DIR.glob("*.yaml")):
        data = read_yaml(path)
        if not isinstance(data, dict) or data.get("kind") == "pair":
            continue
        out.append(
            {
                "profile_id": data["profile_id"],
                "version": data["version"],
                "kind": data["kind"],
                "kind_label": kind_label.get(data["kind"], data["kind"]),
                "topic": data.get("topic"),
                "title": data.get("title", data["profile_id"]),
                "description": (data.get("description") or "").strip(),
                "expected_sheet": data.get("expected_sheet"),
            }
        )
    out.sort(key=lambda p: (p["topic"] != "ipc", p["profile_id"]))
    return out


# --------------------------------------------------------------------------
# Enmiendas de simulación
# --------------------------------------------------------------------------


def save_override(case_id: str, profile: dict[str, Any], note: str) -> Path:
    data = {k: v for k, v in profile.items() if not k.startswith("_")}
    data["_simulation_note"] = note
    path = OVERRIDE_DIR / f"{case_id}.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, allow_unicode=True, sort_keys=False)
    return path


def clear_override(case_id: str) -> bool:
    path = OVERRIDE_DIR / f"{case_id}.yaml"
    if path.exists():
        path.unlink()
        return True
    return False


def has_override(case_id: str) -> bool:
    return (OVERRIDE_DIR / f"{case_id}.yaml").exists()


# --------------------------------------------------------------------------
# Manifiesto del snapshot
# --------------------------------------------------------------------------


def load_manifest() -> dict[str, Any]:
    return load_json(MANIFEST_FILE)


def manifest_item(item_id: str) -> dict[str, Any]:
    for item in load_manifest()["items"]:
        if item["id"] == item_id:
            return item
    raise ConfigError(f"ítem de manifiesto desconocido: {item_id}")


# --------------------------------------------------------------------------
# Casos de la lista cerrada
# --------------------------------------------------------------------------


def load_cases() -> list[dict[str, Any]]:
    return load_json(CASES_FILE)["cases"]


def load_case(case_id: str) -> dict[str, Any]:
    for case in load_cases():
        if case["id"] == case_id:
            return case
    raise ConfigError(f"caso desconocido en la lista cerrada: {case_id}")


# --------------------------------------------------------------------------
# Reglas, justificaciones y decisiones
# --------------------------------------------------------------------------


def load_rules() -> dict[str, Any]:
    return load_json(RULE_DIR / "rules.json")


def rule_meta(rules_doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {rule["id"]: rule for rule in rules_doc["rules"]}


def load_justifications() -> dict[str, Any]:
    return load_json(JUSTIFICATION_FILE)


def justification_for(case_id: str, rule_id: str) -> dict[str, Any] | None:
    entry = load_justifications().get("justifications", {}).get(case_id, {})
    return entry.get(rule_id)


def save_justification(case_id: str, rule_id: str, payload: dict[str, Any]) -> None:
    data = load_justifications()
    data.setdefault("justifications", {}).setdefault(case_id, {})[rule_id] = payload
    dump_json(data, JUSTIFICATION_FILE)


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
