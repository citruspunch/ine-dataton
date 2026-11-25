"""Reglas de cálculo del simulador, en un solo lugar y verificables con pytest.

La aplicación web replica estas fórmulas en TypeScript; este módulo es la
referencia para las pruebas y para cualquier consumidor de los datos.
"""

from __future__ import annotations

from collections.abc import Iterable

from .cba import DAYS_PER_MONTH, cost_per_1000_kcal

MIN_HOUSEHOLD_MEMBERS = 1
MAX_HOUSEHOLD_MEMBERS = 8


def validate_members(members: int) -> int:
    """El simulador admite hogares de 1 a 8 integrantes."""
    if isinstance(members, bool) or not isinstance(members, int):
        raise TypeError("El número de integrantes debe ser un entero")
    if not MIN_HOUSEHOLD_MEMBERS <= members <= MAX_HOUSEHOLD_MEMBERS:
        raise ValueError(
            f"El número de integrantes debe estar entre "
            f"{MIN_HOUSEHOLD_MEMBERS} y {MAX_HOUSEHOLD_MEMBERS}"
        )
    return members


def monthly_cost_per_capita(daily_cost: float) -> float:
    """Costo mensual per cápita = costo diario × 30 (regla del PRD)."""
    return float(daily_cost) * DAYS_PER_MONTH


def household_monthly_cost(daily_cost_per_capita: float, members: int) -> float:
    """Costo mensual del hogar = costo diario per cápita × 30 × integrantes."""
    return monthly_cost_per_capita(daily_cost_per_capita) * validate_members(members)


def household_daily_kcal(kcal_per_capita: float, members: int) -> float:
    """Energía diaria cubierta por la canasta para todo el hogar."""
    return float(kcal_per_capita) * validate_members(members)


def basket_cost_per_1000_kcal(items: Iterable[tuple[float, float]]) -> float | None:
    """Costo de 1 000 kcal de una canasta, excluyendo productos de 0 kcal.

    Se excluye el producto de ambos lados de la fracción: ni su costo ni su kcal
    entran. Sin esta exclusión, el agua purificada y la sal (que cuestan pero no
    aportan energía) inflarían artificialmente el costo por 1 000 kcal.
    """
    cost = 0.0
    kcal = 0.0
    for item_cost, item_kcal in items:
        if item_kcal is None or float(item_kcal) <= 1e-9:
            continue
        cost += float(item_cost)
        kcal += float(item_kcal)
    if kcal <= 0:
        return None
    return cost / kcal * 1000.0


__all__ = [
    "MAX_HOUSEHOLD_MEMBERS",
    "MIN_HOUSEHOLD_MEMBERS",
    "basket_cost_per_1000_kcal",
    "cost_per_1000_kcal",
    "household_daily_kcal",
    "household_monthly_cost",
    "monthly_cost_per_capita",
    "validate_members",
]
