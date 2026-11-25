"""Orden cronológico de meses en español y periodos comparables."""

from __future__ import annotations

import random

import pytest

from ine_basket.months import (
    FIRST_COMPARABLE_PERIOD,
    SPANISH_MONTHS,
    assert_comparable_period,
    month_index,
    month_name,
    month_number,
    month_sort_key,
    parse_period,
    period,
    period_range,
    shift_period,
)


def test_septiembre_sorts_before_octubre_not_alphabetically() -> None:
    labels = ["Octubre", "Septiembre"]
    assert sorted(labels) == ["Octubre", "Septiembre"]  # el orden alfabético es incorrecto
    assert sorted(labels, key=lambda name: month_number(name)) == ["Septiembre", "Octubre"]


def test_all_months_sort_chronologically_from_shuffled_names() -> None:
    shuffled = list(SPANISH_MONTHS)
    random.Random(2024).shuffle(shuffled)
    ordered = sorted(shuffled, key=month_number)
    assert ordered == list(SPANISH_MONTHS)


def test_sort_key_uses_year_then_month_number() -> None:
    records = [
        (2024, "Octubre"),
        (2024, "Septiembre"),
        (2025, "Enero"),
        (2024, "Diciembre"),
    ]
    ordered = sorted(records, key=lambda item: month_sort_key(*item))
    assert ordered == [
        (2024, "Septiembre"),
        (2024, "Octubre"),
        (2024, "Diciembre"),
        (2025, "Enero"),
    ]


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("Enero", 1),
        ("febrero", 2),
        ("  Marzo ", 3),
        ("Septiembre", 9),
        ("Setiembre", 9),
        ("SEPTIEMBRE", 9),
        ("Diciembre.", 12),
    ],
)
def test_month_number_accepts_spanish_variants(label: str, expected: int) -> None:
    assert month_number(label) == expected


@pytest.mark.parametrize("value", ["", "Moisés", "13", "Septiembre 2024"])
def test_month_number_rejects_unknown_values(value: str) -> None:
    with pytest.raises(ValueError):
        month_number(value)


def test_month_name_round_trip() -> None:
    for number in range(1, 13):
        assert month_number(month_name(number)) == number


def test_period_helpers_cross_year_boundaries() -> None:
    assert period(2024, "Septiembre") == "2024-09"
    assert parse_period("2026-10") == (2026, 10)
    assert shift_period("2025-01", -1) == "2024-12"
    assert shift_period("2025-12", 1) == "2026-01"
    assert shift_period("2026-01", -12) == "2025-01"
    assert month_index(2025, 1) - month_index(2024, 12) == 1
    assert period_range("2026-09", "2026-11") == ["2026-09", "2026-10", "2026-11"]


def test_period_before_2024_is_not_comparable() -> None:
    assert FIRST_COMPARABLE_PERIOD == "2024-01"
    with pytest.raises(ValueError, match="anterior"):
        assert_comparable_period("2023-12")
    assert_comparable_period("2024-01")
