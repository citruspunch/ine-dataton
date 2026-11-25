"""Datos de la CBA: periodos, escalado, agrupación y productos sin calorías."""

from __future__ import annotations

import pytest

from ine_basket.cba import REFERENCE_KCAL
from ine_basket.months import month_index
from ine_basket.simulator import basket_cost_per_1000_kcal, household_monthly_cost


def test_both_baskets_cover_the_same_34_chronological_periods(urban, rural) -> None:
    expected = ["2024-01", "2024-02", "2024-03", "2024-09", "2024-10", "2025-01", "2026-10"]
    assert len(urban.periods) == len(rural.periods) == 34
    assert urban.periods == rural.periods
    for label in expected:
        assert label in urban.periods

    indices = [month_index(int(label[:4]), int(label[5:])) for label in urban.periods]
    assert indices == sorted(indices)
    # Diciembre 2024 precede a enero 2025; "Septiembre" no se ordena tras "Octubre".
    assert urban.periods.index("2024-09") < urban.periods.index("2024-10")
    assert urban.periods.index("2024-12") < urban.periods.index("2025-01")


def test_monthly_cost_equals_daily_times_thirty(urban, rural) -> None:
    for bundle in (urban, rural):
        for row in bundle.costs.itertuples(index=False):
            assert row.monthly_cost == pytest.approx(row.daily_cost * 30, rel=1e-12)
            assert row.published_monthly_cost == pytest.approx(row.monthly_cost, abs=0.011)


def test_household_cost_scales_by_members_and_area(urban, rural) -> None:
    jan_urban = urban.costs.iloc[0]
    jan_rural = rural.costs.iloc[0]
    assert household_monthly_cost(jan_urban.daily_cost, 1) == pytest.approx(846.30, abs=0.01)
    assert household_monthly_cost(jan_urban.daily_cost, 4) == pytest.approx(3385.20, abs=0.05)
    assert household_monthly_cost(jan_rural.daily_cost, 4) == pytest.approx(2617.20, abs=0.05)
    assert household_monthly_cost(jan_urban.daily_cost, 4) > household_monthly_cost(
        jan_rural.daily_cost, 4
    )


def test_reference_kcal_are_2052_urban_and_2172_rural(urban, rural) -> None:
    for bundle in (urban, rural):
        totals = bundle.products.groupby("period")["kcal_daily"].sum()
        assert totals.nunique() == 1
        assert totals.iloc[0] == pytest.approx(REFERENCE_KCAL[bundle.area], abs=0.01)


def test_product_counts_and_groups(urban, rural) -> None:
    assert urban.products["product"].nunique() == 66
    assert rural.products["product"].nunique() == 60
    assert urban.groups["group"].nunique() == 13
    assert rural.groups["group"].nunique() == 13


def test_each_product_maps_to_one_group_that_reconciles(urban, rural) -> None:
    for bundle in (urban, rural):
        mapping = bundle.product_groups.set_index("product")["group"]
        assert mapping.index.is_unique
        for period, chunk in bundle.products.groupby("period"):
            target = bundle.groups[bundle.groups["period"] == period].set_index("group")
            derived = chunk.groupby("group")["kcal_daily"].sum()
            for group, kcal in derived.items():
                assert kcal == pytest.approx(target.at[group, "kcal_daily"], abs=1e-6), (
                    f"{bundle.area} {period} {group}"
                )
        # La hoja de grupos del INE y la suma de productos difieren sólo por redondeo.
        assert bundle.max_group_cost_gap < 0.07


def test_zero_kcal_products_are_flagged_and_mapped(urban, rural) -> None:
    for bundle in (urban, rural):
        zero = bundle.products[bundle.products["zero_kcal"]]
        assert set(zero["product"]) == {"Agua purificada", "Sal"}
        mapping = bundle.product_groups.set_index("group")["product"]
        assert "Agua purificada" in mapping.loc["Bebidas no alcohólicas"].tolist()
        assert "Sal" in mapping.loc["Productos alimenticios N.E.P."].tolist()
        # Nunca se calcula un costo por 1000 kcal para sal o agua.
        assert zero["cost_per_1000_kcal"].isna().all()


def test_urban_basket_cost_per_1000_kcal_excludes_water_and_salt(urban) -> None:
    jan = urban.products[urban.products["period"] == "2024-01"]
    excluding = basket_cost_per_1000_kcal(zip(jan["cost_daily"], jan["kcal_daily"], strict=True))
    including = jan["cost_daily"].sum() / jan["kcal_daily"].sum() * 1000
    assert excluding == pytest.approx(12.3966, rel=1e-4)
    assert excluding < including - 1.3
    water = jan[jan["product"] == "Agua purificada"].iloc[0]
    assert water.cost_daily > 2.7  # su costo no puede atribuirse a kcal de otros alimentos
