"""Human gate, decision log and publication to the reduced snapshot.

The gate promises neither a cryptographic signature nor authentication: it
keeps a local record of the sign-off and binds the decision to a digest of the
technical basis.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from . import config
from .rules import validate
from .model import WARNING, FAILURE, NOT_EVALUATED, ValidationResult

APPROVED = ("habilitado", "aprobar_con_excepcion")

DECISION_LABEL = {
    "habilitado": "Habilitado",
    "aprobar_con_excepcion": "Aprobado con excepción",
    "rechazar": "Rechazado",
    "revocado": "Revocado",
}


class GateError(Exception):
    pass


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------
# Receipt
# --------------------------------------------------------------------------


def write_receipt(
    result: ValidationResult,
    subject: Any,
    profile: dict[str, Any],
    rules_doc: dict[str, Any],
    decision: dict[str, Any] | None,
) -> Path:
    manifest = config.load_manifest()
    display = profile.get("display", {})
    item = subject.items[0] if subject.items else {}
    payload = {
        "snapshot_id": manifest["snapshot_id"],
        "source_id": item.get("source_id"),
        "resource_id": item.get("resource_id"),
        "origin": item.get("origin", "snapshot"),
        "period": display.get("period"),
        "base": display.get("base"),
        "unit": display.get("unit"),
        "source_url": item.get("source_url"),
        "downloaded_at_utc": item.get("downloaded_at_utc"),
        "sha256": item.get("sha256"),
        "profile_version": f"{profile['profile_id']}@{profile['version']}",
        "rules_version": rules_doc["rules_version"],
        "findings": [f.to_dict() for f in result.findings],
        "comparisons": [c.to_private_dict() for c in result.comparisons],
        "coverage": result.coverage,
        "state": result.state,
        "digest": result.digests["validation_digest"],
    }
    receipt: dict[str, Any] = {
        "receipt_id": f"rec-{manifest['snapshot_id']}-{result.case_id}",
        "generated_at_utc": utc_now(),
        "technical_payload": payload,
        "decision_log": None,
    }
    if decision:
        receipt["decision_log"] = {
            "decision_id": decision.get("decision_id"),
            "decided_at_utc": decision.get("decided_at_utc"),
            "operator": decision.get("operator"),
            "rationale": decision.get("rationale"),
            "gate_decision": decision.get("gate_decision"),
            "decision_basis_digest": decision.get("decision_basis_digest"),
            "justifications": decision.get("justifications") or {},
            "still_valid": decision.get("decision_basis_digest")
            == result.digests["validation_digest"],
        }
    config.dump_json(receipt, config.RECEIPT_DIR / f"{result.case_id}.json")
    return config.RECEIPT_DIR / f"{result.case_id}.json"


# --------------------------------------------------------------------------
# Preconditions
# --------------------------------------------------------------------------


def blocking_reasons(result: ValidationResult) -> list[str]:
    """Reasons the gate cannot enable. Empty list = can be enabled."""
    problems: list[str] = []

    if result.state in ("borrador", "cerrado"):
        problems.append(f"estado {result.state}: no hay base para habilitar")

    for finding in result.findings:
        if finding.critical and finding.status in (FAILURE, NOT_EVALUATED):
            problems.append(f"{finding.rule_id} crítica en {finding.status}")
        if finding.status == WARNING and not finding.justified:
            problems.append(
                f"{finding.rule_id} es advertencia sin justificación documentada"
            )

    license_entry = result.entity.get("license") or {}
    if result.method != "identity_pair" and not license_entry.get("verified"):
        problems.append("licencia no verificada")

    if not result.coverage.get("complete"):
        problems.append("hay reglas críticas no evaluadas")

    return problems


preconditions = blocking_reasons


def pending_warnings(result: ValidationResult) -> list[dict[str, Any]]:
    return [
        {
            "rule_id": f.rule_id,
            "title": f.title,
            "message": f.message,
            "justified": f.justified,
        }
        for f in result.findings
        if f.status == WARNING
    ]


# --------------------------------------------------------------------------
# Decisions
# --------------------------------------------------------------------------


def _save_justifications(
    case_id: str, justifications: dict[str, dict[str, Any]] | None
) -> None:
    for rule_id, payload in (justifications or {}).items():
        owner = (payload.get("owner") or "").strip()
        reason = (payload.get("reason") or "").strip()
        if not owner or not reason:
            raise GateError(
                f"la advertencia {rule_id} necesita dueño y motivo para justificarse"
            )
        config.save_justification(
            case_id,
            rule_id,
            {
                "owner": owner,
                "reason": reason,
                "date": utc_now()[:10],
                "policy": payload.get("policy") or "sin referencia",
            },
        )


def _append_decision(record: dict[str, Any]) -> None:
    config.DECISION_DIR.mkdir(parents=True, exist_ok=True)
    with open(config.DECISIONS_FILE, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def decide(
    case_id: str,
    operator: str,
    rationale: str,
    decision: str = "aprobar",
    justifications: dict[str, dict[str, Any]] | None = None,
) -> ValidationResult:
    """Record a human decision. `decision`: aprobar | aprobar_con_excepcion | rechazar.

    The decision values are the wire vocabulary persisted in the decision log.
    """
    operator = (operator or "").strip()
    rationale = (rationale or "").strip()
    if not operator:
        raise GateError("el responsable del gate es obligatorio")
    if len(rationale) < 10:
        raise GateError("el motivo de la decisión debe ser explícito")

    _save_justifications(case_id, justifications)
    result = validate(case_id)

    if decision == "rechazar":
        record = _record(
            case_id, operator, rationale, "rechazar", result, justifications
        )
        _append_decision(record)
        remove_public_aggregate(case_id)
        return validate(case_id)

    if decision not in ("aprobar", "aprobar_con_excepcion"):
        raise GateError(f"decisión desconocida: {decision}")

    problems = blocking_reasons(result)
    if problems:
        raise GateError("; ".join(problems))

    if decision == "aprobar_con_excepcion" and not pending_warnings(result):
        # Without warnings there is no exception to document.
        decision = "aprobar"

    stored = "habilitado" if decision == "aprobar" else decision
    record = _record(case_id, operator, rationale, stored, result, justifications)
    _append_decision(record)

    final = validate(case_id)
    if final.state != "habilitado_para_consulta":
        raise GateError(
            f"la decisión se registró pero el estado final es {final.state}; "
            "revise el digest"
        )
    write_public_aggregate(final)
    return final


def _record(
    case_id: str,
    operator: str,
    rationale: str,
    gate_decision: str,
    result: ValidationResult,
    justifications: dict[str, dict[str, Any]] | None,
) -> dict[str, Any]:
    previous = [d for d in config.load_decisions() if d.get("case_id") == case_id]
    return {
        "decision_id": f"dec-{case_id}-{len(previous) + 1:03d}",
        "case_id": case_id,
        "decided_at_utc": utc_now(),
        "operator": operator,
        "rationale": rationale,
        "gate_decision": gate_decision,
        "decision_basis_digest": result.digests["decision_basis_digest"],
        "rules_version": config.load_rules()["rules_version"],
        "profile_version": result.entity.get("profile"),
        "justifications": {
            key: {"owner": val.get("owner"), "reason": val.get("reason")}
            for key, val in (justifications or {}).items()
        },
    }


def promote(case_id: str, operator: str, rationale: str) -> ValidationResult:
    """CLI compatibility: approve without an exception."""
    return decide(case_id, operator, rationale, "aprobar")


def revoke(case_id: str, operator: str, rationale: str) -> None:
    result = validate(case_id, write_receipt=False)
    record = _record(case_id, operator, rationale, "revocado", result, None)
    _append_decision(record)
    remove_public_aggregate(case_id)


# --------------------------------------------------------------------------
# Public snapshot
# --------------------------------------------------------------------------


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
    payload["published_at_utc"] = utc_now()
    payload["notice"] = (
        "Validación técnica. No certifica, no corrige, no publica en CKAN y no "
        "constituye aprobación del INE."
    )
    config.dump_json(payload, path)
    write_public_receipt(result, payload)
    _rebuild_index()
    return path


def public_receipt_path(case_id: str) -> Path:
    return config.PUBLIC_DIR / "receipts" / f"{case_id}.json"


def write_public_receipt(result: ValidationResult, payload: dict[str, Any]) -> Path:
    """Public receipt: same structure as the private one, without private evidence."""
    decision = config.latest_decision(result.case_id) or {}
    snapshot_id = config.load_manifest()["snapshot_id"]
    receipt = {
        "receipt_id": f"rec-{snapshot_id}-{result.case_id}",
        "generated_at_utc": utc_now(),
        "technical_payload": {
            "snapshot_id": snapshot_id,
            "source_id": result.entity.get("source_id"),
            "resource_id": result.entity.get("resource_id"),
            "period": (result.entity.get("display") or {}).get("period"),
            "base": (result.entity.get("display") or {}).get("base"),
            "unit": (result.entity.get("display") or {}).get("unit"),
            "source_url": result.entity.get("source_url"),
            "downloaded_at_utc": result.entity.get("downloaded_at_utc"),
            "sha256": result.entity.get("sha256"),
            "profile_version": result.entity.get("profile"),
            "rules_version": config.load_rules()["rules_version"],
            "findings": [f.to_dict() for f in result.findings],
            "comparisons": [c.to_public_dict() for c in result.comparisons],
            "coverage": result.coverage,
            "state": result.state,
            "digest": result.digests["validation_digest"],
        },
        "decision_log": {
            "decided_at_utc": decision.get("decided_at_utc"),
            "operator": decision.get("operator"),
            "rationale": decision.get("rationale"),
            "gate_decision": decision.get("gate_decision"),
            "decision_basis_digest": decision.get("decision_basis_digest"),
        }
        if decision
        else None,
    }
    path = public_receipt_path(result.case_id)
    config.dump_json(receipt, path)
    return path


def remove_public_aggregate(case_id: str) -> None:
    path = aggregate_path(case_id)
    if path.exists():
        path.unlink()
    _rebuild_index()


def _is_synthetic(entity: dict[str, Any], case_id: str) -> bool:
    if entity.get("kind") == "par de recursos":
        return True
    item_id = entity.get("manifest_item")
    if not item_id:
        return False
    try:
        return bool(config.manifest_item(item_id).get("synthetic"))
    except config.ConfigError:
        return True


def _rebuild_index() -> None:
    aggregates = []
    directory = config.PUBLIC_DIR / "aggregates"
    if directory.exists():
        for path in sorted(directory.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            entity = data.get("entity", {})
            aggregates.append(
                {
                    "case_id": data["case_id"],
                    "label": data["label"],
                    "state": data["state"],
                    "state_text": data["state_text"],
                    "digest": data["digest"],
                    "file": f"aggregates/{path.name}",
                    "synthetic": _is_synthetic(entity, data["case_id"]),
                    "origin": entity.get("origin", "snapshot"),
                    "period": (entity.get("display") or {}).get("period"),
                    "title": entity.get("title") or data["label"],
                }
            )
    index = {
        "snapshot_id": config.load_manifest()["snapshot_id"],
        "generated_at_utc": utc_now(),
        "aggregates": aggregates,
    }
    config.PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    config.dump_json(index, config.PUBLIC_DIR / "index.json")


def _quarantine(case_id: str, reason: str) -> Path | None:
    path = aggregate_path(case_id)
    if not path.exists():
        return None
    config.QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
    data = json.loads(path.read_text(encoding="utf-8"))
    data["quarantine_reason"] = reason
    data["quarantined_at_utc"] = utc_now()
    target = config.QUARANTINE_DIR / f"{case_id}.json"
    config.dump_json(data, target)
    path.unlink()
    _rebuild_index()
    return target


def all_subject_ids() -> list[str]:
    """Closed-list cases plus the files uploaded during the session."""
    from . import store

    return [case["id"] for case in config.load_cases()] + [
        upload["id"] for upload in store.list_uploads()
    ]


def verify() -> list[dict[str, Any]]:
    """Recompute digests, withdraw unsupported aggregates and validate decisions."""
    report = []
    for subject_id in all_subject_ids():
        result = validate(subject_id, write_receipt=False)
        decision = config.latest_decision(subject_id)
        entry = {
            "case_id": subject_id,
            "state": result.state,
            "digest": result.digests["decision_basis_digest"],
            "decision": decision,
            "decision_valid": None,
            "in_public_snapshot": aggregate_path(subject_id).exists(),
            "quarantined": False,
            "override": config.has_override(subject_id),
        }
        if decision:
            entry["decision_valid"] = (
                decision.get("decision_basis_digest") == entry["digest"]
                and decision.get("gate_decision") in APPROVED
            )

        if entry["in_public_snapshot"] and not entry["decision_valid"]:
            reason = (
                "no hay decisión que sostenga el agregado"
                if decision is None
                else "el digest del basis cambió: archivo, perfil, reglas o hallazgos"
            )
            _quarantine(subject_id, reason)
            entry["in_public_snapshot"] = False
            entry["quarantined"] = True

        report.append(entry)
    return report
