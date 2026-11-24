"""P0.3: comparabilidad del IPC y comparador seguro."""

from __future__ import annotations

import json

import pytest

from idt import engine, public_api
from idt.model import OK


def test_contrato_ipc_completo():
    result = engine.validate("ipc_empalme", write_receipt=False)
    assert result.coverage["complete"]
    assert [f.status for f in result.findings] == [OK] * len(result.findings)
    assert (
        result.entity["sha256"]
        == "d0101e366ee6d6bb02345db64b8c725c0a4c65ee85aa800d751d41b8381664d4"
    )


def test_comparacion_valida_usa_la_variacion_publicada():
    result = engine.validate("ipc_empalme", write_receipt=False)
    valid = next(c for c in result.comparisons if c.comparison_id == "mensual_ene_2025")
    assert valid.status == "ok"
    assert valid.public_evidence["computed_pct"] == pytest.approx(0.501463, abs=1e-6)
    assert valid.public_evidence["published_pct"] == pytest.approx(0.501463, abs=1e-6)
    assert valid.public_evidence["published_cell"] == "G504"


def test_comparacion_invalida_se_bloquea():
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


def test_el_numero_invalido_no_entra_en_la_evidencia_publica():
    result = engine.validate("ipc_empalme", write_receipt=False)
    public = json.dumps(result.to_public_dict(), ensure_ascii=False)
    assert "0.6738" not in public
    assert "0,67" not in public
    blocked = next(
        c for c in result.comparisons if c.comparison_id == "cruce_bases_e_f"
    )
    assert "computed_pct" not in blocked.public_evidence


def test_comparador_publico_entrega_la_cifra_publicada(seeded):
    result = public_api.compare("ipc_empalme", "f", "2024-12", "f", "2025-01")
    assert result["status"] == "ok"
    assert result["published_pct"] == pytest.approx(0.501463, abs=1e-6)
    assert result["published_cell"] == "G504"
    assert result["period"] == "2025-01"
    assert result["previous_period"] == "2024-12"
    assert "computed_pct" not in result


def test_comparador_publico_bloquea_bases_distintas(seeded):
    result = public_api.compare("ipc_empalme", "e", "2024-12", "f", "2025-01")
    assert result["status"] == "bloqueada"
    assert result["code"] == "base_incompatible"
    assert "published_pct" not in result
    assert "0.6738" not in json.dumps(result)


def test_comparador_bloquea_periodos_no_contiguos(seeded):
    result = public_api.compare(
        "ipc_regional", "republica", "2025-01", "republica", "2025-06"
    )
    assert result["status"] == "bloqueada"
    assert result["code"] == "periodos_no_contiguos"


def test_recurso_sin_variacion_publicada_no_inventa(seeded):
    result = public_api.compare(
        "ipc_regional", "republica", "2025-01", "republica", "2025-02"
    )
    assert result["status"] == "bloqueada"
    assert result["code"] == "sin_variacion_publicada"
    assert "published_pct" not in result


def test_consultar_serie_ipc(seeded):
    data = public_api.consultar_serie_ipc("2024-01", "2025-12")
    assert data["status"] == "ok"
    assert data["series_id"] == "f"
    assert [p["period"] for p in data["points"]] == ["2024-12", "2025-01"]
    assert data["points"][-1]["published_variation_pct"] == pytest.approx(
        0.5014633313243735, abs=1e-12
    )


def test_consultar_serie_fuera_de_rango(seeded):
    with pytest.raises(public_api.PublicError) as exc:
        public_api.consultar_serie_ipc("1990-01", "1990-12")
    assert exc.value.code == "periodo_no_publicado"
