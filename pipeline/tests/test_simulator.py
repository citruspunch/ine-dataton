"""Cálculos del simulador: escalado del hogar y exclusión de alimentos sin kcal."""

from __future__ import annotations

import pytest

from ine_basket.cba import cost_per_1000_kcal
from ine_basket.simulator import (
    basket_cost_per_1000_kcal,
    household_daily_kcal,
    household_monthly_cost,
    monthly_cost_per_capita,
    validate_members,
)


def test_monthly_cost_is_daily_times_thirty() -> None:
    assert monthly_cost_per_capita(28.21) == pytest.approx(846.30)
    assert monthly_cost_per_capita(30.154333) == pytest.approx(904.62999)


@pytest.mark.parametrize("members", range(1, 9))
def test_household_cost_scales_linearly_with_members(members: int) -> None:
    daily = 28.21
    assert household_monthly_cost(daily, members) == pytest.approx(daily * 30 * members)
    assert household_daily_kcal(2052, members) == pytest.approx(2052 * members)


def test_household_cost_matches_hand_calculation() -> None:
    # Octubre 2026, CBA urbana: Q32.898279/día per cápita, hogar de 4 integrantes.
    assert household_monthly_cost(32.898279, 4) == pytest.approx(3947.79348, rel=1e-9)


@pytest.mark.parametrize("members", [0, 9, -1, 100])
def test_household_size_is_limited_to_one_through_eight(members: int) -> None:
    with pytest.raises(ValueError, match="entre 1 y 8"):
        validate_members(members)


def test_household_size_must_be_integer() -> None:
    with pytest.raises(TypeError):
        validate_members(3.5)  # type: ignore[arg-type]


def test_product_with_zero_kcal_has_no_cost_per_1000_kcal() -> None:
    assert cost_per_1000_kcal(0.011028, 0.0) is None
    assert cost_per_1000_kcal(2.760072, 0.0) is None


def test_basket_cost_per_1000_kcal_ignores_zero_kcal_items() -> None:
    # Arroz: Q0.324 por 66.7 kcal; agua: Q2.76 por 0 kcal.
    value = basket_cost_per_1000_kcal([(0.3243, 66.716), (2.7601, 0.0)])
    assert value == pytest.approx(0.3243 / 66.716 * 1000)


def test_ignoring_zero_kcal_items_changes_the_result() -> None:
    including_cost = basket_cost_per_1000_kcal([(25.4378 + 2.7711, 2052.0)])
    excluding_cost = basket_cost_per_1000_kcal([(25.4378, 2052.0), (2.7711, 0.0)])
    assert including_cost is not None and excluding_cost is not None
    assert excluding_cost == pytest.approx(12.3966, rel=1e-4)
    assert including_cost > excluding_cost + 1.3


def test_basket_without_calories_returns_none() -> None:
    assert basket_cost_per_1000_kcal([(3.0, 0.0), (0.1, 0.0)]) is None
