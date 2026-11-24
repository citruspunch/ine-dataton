"""Gate humano, bitácora de decisiones y publicación al snapshot reducido.

El gate no promete firma criptográfica ni autenticación: deja constancia local
del visto bueno y liga la decisión a un digest del basis técnico.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from . import config
from .engine import validate
from .model import ADVERTENCIA, FALLA, NO_EVALUADO, ValidationResult


class GateError(Exception):
    pass


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _append_decision(record: dict[str, Any]) -> None:
    config.DECISION_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.DECISIONS_FILE, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def preconditions(result: ValidationResult) -> list[str]:
    """Motivos por los que el gate no puede habilitar. Lista vacía = habilitable."""
    problems: list[str] = []

    if result.state in ("borrador", "cerrado"):
        problems.append(f"estado {result.state}: no hay base para habilitar")

    for finding in result.findings:
        if finding.critical and finding.status in (FALLA, NO_EVALUADO):
            problems.append(f"{finding.rule_id} crítica en {finding.status}")
        if finding.status == ADVERTENCIA and not finding.justified:
            problems.append(
                f"{finding.rule_id} es advertencia sin justificación documentada"
            )

    license_entry = result.entity.get("license") or {}
    if result.method != "identity_pair" and not license_entry.get("verified"):
        problems.append("licencia no verificada")

    if not result.coverage.get("complete"):
        problems.append("hay reglas críticas no evaluadas")

    return problems


def promote(case_id: str, operator: str, rationale: str) -> ValidationResult:
    result = validate(case_id)
    problems = preconditions(result)
    if problems:
        raise GateError("; ".join(problems))

    previous = [d for d in config.load_decisions() if d.get("case_id") == case_id]
    record = {
        "decision_id": f"dec-{case_id}-{len(previous) + 1:03d}",
        "case_id": case_id,
        "decided_at_utc": _utc_now(),
        "operator": operator,
        "rationale": rationale,
        "gate_decision": "habilitado",
        "decision_basis_digest": result.digests["decision_basis_digest"],
        "rules_version": config.load_rules()["rules_version"],
        "profile_version": result.entity.get("profile") or _pair_profile(result),
    }
    _append_decision(record)

    final = validate(case_id)
    write_public_aggregate(final)
    return final


def revoke(case_id: str, operator: str, rationale: str) -> None:
    result = validate(case_id)
    previous = [d for d in config.load_decisions() if d.get("case_id") == case_id]
    _append_decision(
        {
            "decision_id": f"dec-{case_id}-{len(previous) + 1:03d}",
            "case_id": case_id,
            "decided_at_utc": _utc_now(),
            "operator": operator,
            "rationale": rationale,
            "gate_decision": "revocado",
            "decision_basis_digest": result.digests["decision_basis_digest"],
            "rules_version": config.load_rules()["rules_version"],
            "profile_version": result.entity.get("profile") or _pair_profile(result),
        }
    )
    remove_public_aggregate(case_id)


def _pair_profile(result: ValidationResult) -> str:
    profile = config.load_profile(config.load_case(result.case_id)["profile"])
    return f"{profile['profile_id']}@{profile['version']}"


def aggregate_path(case_id: str) -> Path:
    return config.PUBLIC_DIR / "aggregates" / f"{case_id}.json"


def write_public_aggregate(result: ValidationResult) -> Path:
    if result.state != "habilitado_para_consulta":
        raise GateError(
            f"no se publica un agregado en estado {result.state}: "
            "solo habilitado_para_consulta entra al snapshot público"
        )
    path = aggregate_path(result.case_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = result.to_public_dict()
    payload["published_at_utc"] = _utc_now()
    payload["notice"] = (
        "Validación técnica del prototipo. No certifica, no corrige, no publica en "
        "CKAN y no constituye aprobación del INE."
    )
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    _rebuild_index()
    return path


def remove_public_aggregate(case_id: str) -> None:
    path = aggregate_path(case_id)
    if path.exists():
        path.unlink()
    _rebuild_index()


def _rebuild_index() -> None:
    aggregates = []
    directory = config.PUBLIC_DIR / "aggregates"
    if directory.exists():
        for path in sorted(directory.glob("*.json")):
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            aggregates.append(
                {
                    "case_id": data["case_id"],
                    "label": data["label"],
                    "state": data["state"],
                    "state_text": data["state_text"],
                    "digest": data["digest"],
                    "file": f"aggregates/{path.name}",
                    "synthetic": _is_synthetic(data),
                }
            )
    index = {
        "snapshot_id": config.load_manifest()["snapshot_id"],
        "generated_at_utc": _utc_now(),
        "aggregates": aggregates,
    }
    config.PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.PUBLIC_DIR / "index.json", "w", encoding="utf-8") as fh:
        json.dump(index, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")


def _is_synthetic(data: dict[str, Any]) -> bool:
    entity = data.get("entity", {})
    if entity.get("kind") == "par de recursos":
        return True
    item_id = entity.get("manifest_item")
    if not item_id:
        return False
    try:
        return bool(config.manifest_item(item_id).get("synthetic"))
    except config.ConfigError:
        return False


def _quarantine(case_id: str, reason: str) -> Path | None:
    """Retira del snapshot público un agregado cuya decisión ya no sostiene."""
    path = aggregate_path(case_id)
    if not path.exists():
        return None
    directory = config.REVIEW_DIR / "quarantine"
    directory.mkdir(parents=True, exist_ok=True)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["quarantine_reason"] = reason
    data["quarantined_at_utc"] = _utc_now()
    target = directory / f"{case_id}.json"
    with open(target, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    path.unlink()
    _rebuild_index()
    return target


def verify() -> list[dict[str, Any]]:
    """Recalcula digests, retira agregados insostenibles y valida decisiones."""
    report = []
    for case in config.load_cases():
        result = validate(case["id"], write_receipt=False)
        decision = config.latest_decision(case["id"])
        entry = {
            "case_id": case["id"],
            "state": result.state,
            "digest": result.digests["decision_basis_digest"],
            "decision": decision,
            "decision_valid": None,
            "in_public_snapshot": aggregate_path(case["id"]).exists(),
            "quarantined": False,
        }
        if decision:
            entry["decision_valid"] = (
                decision.get("decision_basis_digest") == entry["digest"]
                and decision.get("gate_decision") == "habilitado"
            )

        if entry["in_public_snapshot"] and not entry["decision_valid"]:
            reason = (
                "no hay decisión que sostenga el agregado"
                if decision is None
                else "el digest del basis cambió: archivo, perfil, reglas o hallazgos"
            )
            _quarantine(case["id"], reason)
            entry["in_public_snapshot"] = False
            entry["quarantined"] = True

        report.append(entry)
    return report
