"""Cell suppression for small counts.

The app applies a conservative statistical-secrecy rule: non-zero counts below
five are not published, and any derived rate whose numerator or denominator is
suppressed is also withheld. The rule is applied to vital-event and school
counts; model-based poverty estimates and administrative money amounts are not
counts and are not suppressed.

This is an implementation choice for the prototype, aligned with the
confidentiality principle of Decreto-Ley 3-85 (Ley de Estadística) and its
regulations. It is not an official INE disclosure-control decision.
"""

from __future__ import annotations

import pandas as pd


SUPPRESSION_THRESHOLD = 5

COUNT_FIELDS: tuple[tuple[str, str], ...] = (
    ("nacimientos_2025", "Nacimientos registrados en 2025"),
    ("defunciones_2025", "Defunciones registradas en 2025"),
    ("defunciones_menores_5_2025", "Defunciones de menores de 5 años en 2025"),
    ("escuelas_2022", "Establecimientos educativos en 2022"),
    ("escuelas_publicas_2022", "Establecimientos públicos en 2022"),
    ("estudiantes_2022", "Estudiantes inscritos en 2022"),
    ("estudiantes_publicos_2022", "Estudiantes en establecimientos públicos en 2022"),
)

COUNT_LABELS = dict(COUNT_FIELDS)

DERIVED_RULES: dict[str, tuple[str, ...]] = {
    "nacimientos_por_escuela_2025": ("nacimientos_2025", "escuelas_2022"),
    "estudiantes_por_escuela_2022": ("estudiantes_2022", "escuelas_2022"),
    "nacimientos_por_100_estudiantes_2025": ("nacimientos_2025", "estudiantes_2022"),
    "tasa_mortalidad_menor_5_2025": (
        "defunciones_menores_5_2025",
        "nacimientos_2025",
    ),
    "tasa_mortalidad_general_2025": ("defunciones_2025", "poblacion_2025"),
}

DERIVED_LABELS = {
    "nacimientos_por_escuela_2025": "Nacimientos por escuela",
    "estudiantes_por_escuela_2022": "Estudiantes por escuela",
    "nacimientos_por_100_estudiantes_2025": "Nacimientos por 100 estudiantes",
    "tasa_mortalidad_menor_5_2025": "Mortalidad de menores de 5 años por 1,000 nacimientos",
    "tasa_mortalidad_general_2025": "Mortalidad general por 1,000 habitantes",
}


def is_small_count(value: object, threshold: int = SUPPRESSION_THRESHOLD) -> bool:
    if value is None or pd.isna(value):
        return False
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False
    return 0 < numeric < threshold


def suppress_count(
    value: object, threshold: int = SUPPRESSION_THRESHOLD
) -> tuple[object, bool]:
    """Return ``(published_value, suppressed)`` for one count cell."""

    if is_small_count(value, threshold):
        return pd.NA, True
    return value, False


def suppress_counts(
    frame: pd.DataFrame,
    threshold: int = SUPPRESSION_THRESHOLD,
) -> tuple[pd.DataFrame, dict]:
    """Null small non-zero counts and add one boolean flag per count field."""

    result = frame.copy()
    by_field: dict[str, int] = {}
    for field, _label in COUNT_FIELDS:
        if field not in result.columns:
            continue
        flag_field = f"{field}_suprimido"
        flags = result[field].map(lambda value: is_small_count(value, threshold))
        result[flag_field] = flags.astype(bool)
        result.loc[flags, field] = pd.NA
        by_field[field] = int(flags.sum())

    total = int(sum(by_field.values()))
    municipalities = 0
    flag_columns = [
        f"{field}_suprimido"
        for field, _ in COUNT_FIELDS
        if f"{field}_suprimido" in result
    ]
    if flag_columns:
        municipalities = int(result[flag_columns].any(axis=1).sum())

    summary = {
        "threshold": threshold,
        "rule": (
            "Se suprimen los conteos no nulos menores que 5. Los ceros se "
            "publican como cero. Las tasas derivadas se suprimen si cualquiera "
            "de sus componentes fue suprimido."
        ),
        "count_fields": [
            {"field": field, "label": label, "suppressed_cells": by_field.get(field, 0)}
            for field, label in COUNT_FIELDS
            if field in result.columns
        ],
        "suppressed_cells_by_field": {k: v for k, v in by_field.items() if v},
        "suppressed_cells_total": total,
        "municipalities_with_suppression": municipalities,
        "legal_basis": (
            "Decreto-Ley 3-85, Ley de Estadística, y sus reglamentos: secreto "
            "estadístico y prohibición de divulgar datos individuales. La "
            "supresión de celdas pequeñas es una salvaguarda adicional."
        ),
        "notes": (
            "La regla de umbral 5 es una decisión conservadora del prototipo, "
            "no una marca oficial de supresión del INE. Las estimaciones de "
            "pobreza y los montos administrativos no son conteos y no se suprimen."
        ),
    }
    return result, summary


def suppress_derived(
    frame: pd.DataFrame,
    rules: dict[str, tuple[str, ...]] | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Withhold derived rates whose components were suppressed or are missing."""

    rules = rules or DERIVED_RULES
    result = frame.copy()
    suppressed: dict[str, int] = {}
    for derived, components in rules.items():
        if derived not in result.columns:
            continue
        flag_field = f"{derived}_suprimido"
        flags = pd.Series(False, index=result.index)
        for component in components:
            component_flag = f"{component}_suprimido"
            if component_flag in result.columns:
                flags = flags | result[component_flag].fillna(False).astype(bool)
            if component in result.columns:
                flags = flags | result[component].isna()
        result[flag_field] = flags.astype(bool)
        result.loc[flags, derived] = pd.NA
        suppressed[derived] = int(flags.sum())

    summary = {
        "derived_fields": [
            {
                "field": field,
                "label": DERIVED_LABELS.get(field, field),
                "suppressed_cells": count,
            }
            for field, count in suppressed.items()
        ],
        "suppressed_cells_total": int(sum(suppressed.values())),
    }
    return result, summary


def suppression_metadata() -> dict:
    return {
        "threshold": SUPPRESSION_THRESHOLD,
        "count_fields": [{"field": f, "label": label} for f, label in COUNT_FIELDS],
        "derived_rules": {
            field: list(components) for field, components in DERIVED_RULES.items()
        },
        "legal_basis": ("Decreto-Ley 3-85, Ley de Estadística, y sus reglamentos."),
        "ui_label": "Suprimido (<5)",
    }
