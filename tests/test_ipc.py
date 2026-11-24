"""P0.3: IPC comparability and the safe comparator."""

from __future__ import annotations

import json

import pytest

from idt import engine, public_api
from idt.model import OK


def test_full_ipc_contract():
    result = engine.validate("ipc_empalme", write_receipt=False)
    assert result.coverage["complete"]
    assert [f.status for f in result.findings] == [OK] * len(result.findings)
    assert (
        result.entity["sha256"]
        == "d0101e366ee6d6bb02345db64b8c725c0a4c65ee85aa800d751d41b8381664d4"
    )


def test_valid_comparison_uses_published_variation():
    result = engine.validate("ipc_empalme", write_receipt=False)
    valid = next(c for c in result.comparisons if c.comparison_id == "mensual_ene_2025")
    assert valid.status == "ok"
    assert valid.public_evidence["computed_pct"] == pytest.approx(0.501463, abs=1e-6)
    assert valid.public_evidence["published_pct"] == pytest.approx(0.501463, abs=1e-6)
    assert valid.public_evidence["published_cell"] == "G504"


def test_invalid_comparison_is_blocked():
    result = engine.validate("ipc_empalme", write_receipt=False)
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
    result = engine.validate("ipc_empalme", write_receipt=False)
    public = json.dumps(result.to_public_dict(), ensure_ascii=False)
    assert "0.6738" not in public
    assert "0,67" not in public
    blocked = next(
        c for c in result.comparisons if c.comparison_id == "cruce_bases_e_f"
    )
    assert "computed_pct" not in blocked.public_evidence


def test_public_comparator_returns_published_figure(seeded):
    result = public_api.compare("ipc_empalme", "f", "2024-12", "f", "2025-01")
    assert result["status"] == "ok"
    assert result["published_pct"] == pytest.approx(0.501463, abs=1e-6)
    assert result["published_cell"] == "G504"
    assert result["period"] == "2025-01"
    assert result["previous_period"] == "2024-12"
    assert "computed_pct" not in result


def test_public_comparator_blocks_different_bases(seeded):
    result = public_api.compare("ipc_empalme", "e", "2024-12", "f", "2025-01")
    assert result["status"] == "bloqueada"
    assert result["code"] == "base_incompatible"
    assert "published_pct" not in result
    assert "0.6738" not in json.dumps(result)


def test_comparator_blocks_non_contiguous_periods(seeded):
    result = public_api.compare(
        "ipc_regional", "republica", "2025-01", "republica", "2025-06"
    )
    assert result["status"] == "bloqueada"
    assert result["code"] == "periodos_no_contiguos"


def test_resource_without_published_variation_does_not_invent(seeded):
    result = public_api.compare(
        "ipc_regional", "republica", "2025-01", "republica", "2025-02"
    )
    assert result["status"] == "bloqueada"
    assert result["code"] == "sin_variacion_publicada"
    assert "published_pct" not in result


def test_query_ipc_series(seeded):
    data = public_api.query_ipc_series("2024-01", "2025-12")
    assert data["status"] == "ok"
    assert data["series_id"] == "f"
    assert [p["period"] for p in data["points"]] == ["2024-12", "2025-01"]
    assert data["points"][-1]["published_variation_pct"] == pytest.approx(
        0.5014633313243735, abs=1e-12
    )


def test_query_series_out_of_range(seeded):
    with pytest.raises(public_api.PublicError) as exc:
        public_api.query_ipc_series("1990-01", "1990-12")
    assert exc.value.code == "periodo_no_publicado"
