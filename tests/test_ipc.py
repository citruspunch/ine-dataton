"""P0.3: IPC comparability validated at review time."""

from __future__ import annotations

import json

import pytest

from engine import rules
from engine.model import OK


def test_full_ipc_contract():
    result = rules.validate("ipc_empalme", write_receipt=False)
    assert result.coverage["complete"]
    assert [f.status for f in result.findings] == [OK] * len(result.findings)
    assert (
        result.entity["sha256"]
        == "d0101e366ee6d6bb02345db64b8c725c0a4c65ee85aa800d751d41b8381664d4"
    )


def test_valid_comparison_uses_published_variation():
    result = rules.validate("ipc_empalme", write_receipt=False)
    valid = next(c for c in result.comparisons if c.comparison_id == "mensual_ene_2025")
    assert valid.status == "ok"
    assert valid.public_evidence["computed_pct"] == pytest.approx(0.501463, abs=1e-6)
    assert valid.public_evidence["published_pct"] == pytest.approx(0.501463, abs=1e-6)
    assert valid.public_evidence["published_cell"] == "G504"


def test_invalid_comparison_is_blocked():
    result = rules.validate("ipc_empalme", write_receipt=False)
    blocked = next(
        c for c in result.comparisons if c.comparison_id == "cruce_bases_e_f"
    )
    assert blocked.status == "bloqueada"
    assert blocked.private_evidence["computed_pct"] == pytest.approx(
        -0.673802, abs=1e-6
    )
    assert blocked.private_evidence["display_public"] is False
    assert "IPC-01" in blocked.rules


def test_invalid_number_never_reaches_public_evidence():
    result = rules.validate("ipc_empalme", write_receipt=False)
    public = json.dumps(result.to_public_dict(), ensure_ascii=False)
    assert "0.6738" not in public
    assert "0,67" not in public
    blocked = next(
        c for c in result.comparisons if c.comparison_id == "cruce_bases_e_f"
    )
    assert "computed_pct" not in blocked.public_evidence
