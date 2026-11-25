"""IPC: empalme oficial vs. cálculo directo entre bases incompatibles."""

from __future__ import annotations

import pytest


def test_ipc_covers_34_months_in_order(ipc) -> None:
    assert len(ipc.monthly) == 34
    assert ipc.monthly["period"].iloc[0] == "2024-01"
    assert ipc.monthly["period"].iloc[-1] == "2026-10"
    assert ipc.monthly["period"].is_monotonic_increasing


def test_january_2025_official_monthly_variation_is_plus_half_percent(ipc) -> None:
    january = ipc.monthly[ipc.monthly["period"] == "2025-01"].iloc[0]
    assert january.official_monthly_var == pytest.approx(0.501463, abs=1e-5)
    assert round(float(january.official_monthly_var), 2) == 0.50


def test_unspliced_january_2025_would_report_minus_0_67_percent(ipc) -> None:
    january = ipc.monthly[ipc.monthly["period"] == "2025-01"].iloc[0]
    assert january.direct_monthly_var == pytest.approx(-0.6738, abs=1e-3)
    assert round(float(january.direct_monthly_var), 2) == -0.67
    assert january.cross_base_monthly
    assert january.direct_monthly_gap_pp == pytest.approx(-1.1753, abs=1e-3)


def test_link_factor_aligns_the_two_bases(ipc) -> None:
    assert ipc.link_factor == pytest.approx(0.988306, abs=1e-6)
    linked = ipc.dec_2024_index_dec2023_base * ipc.link_factor
    assert linked == pytest.approx(ipc.jan_2025_index_2024_base / 1.00501463, abs=1e-5)
    corrected = (ipc.jan_2025_index_2024_base / linked - 1) * 100
    assert corrected == pytest.approx(ipc.official_jan_2025_monthly_var, abs=1e-6)


def test_direct_monthly_is_only_invalid_at_the_base_break(ipc) -> None:
    cross = ipc.monthly[ipc.monthly["cross_base_monthly"]]
    assert cross["period"].tolist() == ["2025-01"]


def test_direct_interannual_is_invalid_for_all_of_2025(ipc) -> None:
    cross = ipc.monthly[ipc.monthly["cross_base_interannual"]]
    assert len(cross) == 12
    assert set(cross["year"]) == {2025}
    june = ipc.monthly[ipc.monthly["period"] == "2025-06"].iloc[0]
    assert june.direct_interannual_var == pytest.approx(0.5948, abs=1e-3)
    assert june.official_interannual_var == pytest.approx(1.7851, abs=1e-3)
    assert june.direct_interannual_gap_pp == pytest.approx(-1.1903, abs=1e-3)


def test_official_values_match_the_published_splice(ipc) -> None:
    jan_2024 = ipc.monthly[ipc.monthly["period"] == "2024-01"].iloc[0]
    assert jan_2024.official_monthly_var == pytest.approx(0.026406, abs=1e-6)
    oct_2026 = ipc.monthly[ipc.monthly["period"] == "2026-10"].iloc[0]
    assert oct_2026.official_interannual_var == pytest.approx(4.375225, abs=1e-5)
    assert oct_2026.official_accum_var == pytest.approx(3.988552, abs=1e-5)


def test_direct_and_official_agree_inside_a_single_base(ipc) -> None:
    for period in ("2026-01", "2026-06", "2026-10"):
        row = ipc.monthly[ipc.monthly["period"] == period].iloc[0]
        assert not row.cross_base_monthly
        assert not row.cross_base_interannual
        assert row.direct_monthly_var == pytest.approx(row.official_monthly_var, abs=1e-6)
        assert row.direct_interannual_var == pytest.approx(row.official_interannual_var, abs=1e-6)


def test_november_2024_revision_does_not_trigger_a_base_alert(ipc) -> None:
    # El archivo base 2023 y el empalme difieren en 0,002 pp por revisión del INE;
    # eso no es un cruce de bases y no debe advertirse como tal.
    november = ipc.monthly[ipc.monthly["period"] == "2024-11"].iloc[0]
    assert not november.cross_base_monthly
    assert abs(november.direct_monthly_gap_pp) < 0.01
