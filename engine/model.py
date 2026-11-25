"""Domain objects of the prototype.

States (PRD 7.4) and their visible labels. There is no "approved by INE".

The string values of states, severities and labels are the Spanish contract
from the PRD: they are persisted in rules, receipts, decisions and the public
snapshot. Only the Python names are English.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

STATE_TEXT = {
    "borrador": "Borrador, no consultable",
    "no_habilitado": "No habilitado para consulta",
    "en_revision": "En revisión",
    "habilitado_para_consulta": "Habilitado para consulta en el prototipo",
    "cerrado": "Cerrado por defecto",
}

# Allowed severities. `no_evaluado` is never used for a clear discrepancy.
OK = "ok"
FAILURE = "falla"
WARNING = "advertencia"
NOT_EVALUATED = "no_evaluado"

SEVERITIES = (OK, FAILURE, WARNING, NOT_EVALUATED)


@dataclass
class Finding:
    rule_id: str
    title: str
    status: str
    critical: bool
    message: str
    evidence: dict[str, Any] = field(default_factory=dict)
    justified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "status": self.status,
            "critical": self.critical,
            "message": self.message,
            "evidence": self.evidence,
            "justified": self.justified,
        }


@dataclass
class Comparison:
    """Outcome of a comparison request (P0.3).

    `private_evidence` may hold the invalid number: it is shown on the review
    screen and never on the public sheet.
    """

    comparison_id: str
    label: str
    status: str  # "ok" | "bloqueada"
    reason: str
    public_evidence: dict[str, Any] = field(default_factory=dict)
    private_evidence: dict[str, Any] = field(default_factory=dict)
    rules: list[str] = field(default_factory=list)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "comparison_id": self.comparison_id,
            "label": self.label,
            "status": self.status,
            "reason": self.reason,
            "evidence": self.public_evidence,
            "rules": self.rules,
        }

    def to_private_dict(self) -> dict[str, Any]:
        out = self.to_public_dict()
        out["private_evidence"] = self.private_evidence
        return out


@dataclass
class ValidationResult:
    case_id: str
    label: str
    method: str
    entity: dict[str, Any]
    findings: list[Finding] = field(default_factory=list)
    comparisons: list[Comparison] = field(default_factory=list)
    state: str = "borrador"
    coverage: dict[str, Any] = field(default_factory=dict)
    digests: dict[str, str] = field(default_factory=dict)
    warnings_justified: bool = True

    @property
    def state_text(self) -> str:
        return STATE_TEXT[self.state]

    def critical(self) -> list[Finding]:
        return [f for f in self.findings if f.critical]

    def to_private_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "label": self.label,
            "method": self.method,
            "entity": self.entity,
            "state": self.state,
            "state_text": self.state_text,
            "coverage": self.coverage,
            "digests": self.digests,
            "findings": [f.to_dict() for f in self.findings],
            "comparisons": [c.to_private_dict() for c in self.comparisons],
        }

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "label": self.label,
            "entity": self.entity,
            "state": self.state,
            "state_text": self.state_text,
            "coverage": self.coverage,
            "digest": self.digests.get("validation_digest"),
            "findings": [f.to_dict() for f in self.findings],
            "comparisons": [c.to_public_dict() for c in self.comparisons],
        }


def derive_state(
    findings: list[Finding],
    license_verified: bool,
    gate_approved: bool,
    warnings_justified: bool,
) -> str:
    """State machine from PRD 7.4, in the documented order.

    Without a verified license the resource closes by default: that is the
    institutionally safe message, even when technical failures are also visible.
    """
    if not license_verified:
        return "cerrado"
    crit = [f for f in findings if f.critical]
    if not crit:
        return "borrador"
    if any(f.status in (FAILURE, NOT_EVALUATED) for f in crit):
        return "no_habilitado"
    if any(f.status == WARNING for f in findings) and not warnings_justified:
        return "en_revision"
    if not gate_approved:
        return "en_revision"
    return "habilitado_para_consulta"


def summarize_coverage(findings: list[Finding]) -> dict[str, Any]:
    total = len(findings)
    crit = [f for f in findings if f.critical]
    evaluated = [f for f in crit if f.status != NOT_EVALUATED]
    by_status: dict[str, int] = {}
    for f in findings:
        by_status[f.status] = by_status.get(f.status, 0) + 1
    return {
        "rules_total": total,
        "critical_total": len(crit),
        "critical_evaluated": len(evaluated),
        "critical_not_evaluated": len(crit) - len(evaluated),
        "complete": len(evaluated) == len(crit),
        "by_status": by_status,
    }
