"""Build the 340-row municipal indicator table.

All joins are explicit left joins from the reference catalogue, followed by a
hard check that the row count is still 340 and that every code is present. That
is deliberate: a silent many-to-one or a dropped municipality is the main
failure mode for a municipal comparison tool.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .normalize import assert_unique_codes
from .suppression import (
    COUNT_LABELS,
    DERIVED_LABELS,
    suppress_counts,
    suppress_derived,
)


# Selectable indicators are the three choices in the top control.
INDICATOR_DEFINITIONS: list[dict] = [
    {
        "key": "crecimiento_poblacional_pct",
        "label": "Crecimiento poblacional proyectado 2025–2035",
        "short_label": "Crecimiento poblacional",
        "unit": "%",
        "format": "percent",
        "direction": "higher",
        "rank": True,
        "sources": ["ine-proyecciones-2035", "ine-proyecciones-2030"],
        "license_summary": "INE, estadísticas públicas. Ver Fuentes y licencias.",
        "description": (
            "Variación porcentual de la población total proyectada entre 2025 y "
            "2035. Un valor mayor indica más presión futura sobre servicios."
        ),
    },
    {
        "key": "nacimientos_por_escuela_2025",
        "label": "Nacimientos por escuela (2025 / 2022)",
        "short_label": "Nacimientos por escuela",
        "unit": "nacimientos por escuela",
        "format": "ratio",
        "direction": "higher",
        "rank": True,
        "sources": ["ine-nacimientos-2025", "mineduc-establecimientos-2022"],
        "license_summary": "INE (estadísticas públicas) + MINEDUC (CC0 1.0).",
        "description": (
            "Nacimientos de 2025 por establecimiento educativo existente en "
            "2022. Es una razón de carga, no una medida de alumnos por aula."
        ),
    },
    {
        "key": "asignacion_presion_indice_2026",
        "label": "Presión de la asignación constitucional 2026",
        "short_label": "Presión de asignación",
        "unit": "índice (promedio nacional = 1)",
        "format": "index",
        "direction": "higher",
        "rank": True,
        "sources": ["segeplan-asignacion-2026"],
        "license_summary": "SEGEPLAN CC BY-NC 2.0 (uso no comercial).",
        "description": (
            "Asignación constitucional promedio nacional por habitante dividida "
            "por la asignación municipal por habitante. Mayor que 1 significa "
            "menos recursos por residente que el promedio nacional. La población "
            "es la usada por SEGEPLAN en el cálculo oficial."
        ),
    },
    {
        "key": "estudiantes_por_escuela_2022",
        "label": "Estudiantes por escuela (2022)",
        "short_label": "Estudiantes por escuela",
        "unit": "estudiantes por escuela",
        "format": "ratio",
        "direction": "higher",
        "rank": True,
        "sources": ["mineduc-estudiantes-2022", "mineduc-establecimientos-2022"],
        "license_summary": "MINEDUC CC0 1.0.",
        "description": "Matrícula total de 2022 dividida por establecimientos únicos de 2022.",
    },
    {
        "key": "nacimientos_por_100_estudiantes_2025",
        "label": "Nacimientos por 100 estudiantes (2025 / 2022)",
        "short_label": "Nacimientos por 100 estudiantes",
        "unit": "por 100 estudiantes",
        "format": "ratio",
        "direction": "higher",
        "rank": True,
        "sources": ["ine-nacimientos-2025", "mineduc-estudiantes-2022"],
        "license_summary": "INE (estadísticas públicas) + MINEDUC CC0 1.0.",
        "description": "Nacimientos de 2025 por cada 100 estudiantes matriculados en 2022.",
    },
    {
        "key": "tasa_mortalidad_menor_5_2025",
        "label": "Mortalidad de menores de 5 años (por 1,000 nacimientos, 2025)",
        "short_label": "Mortalidad menor de 5",
        "unit": "por 1,000 nacimientos",
        "format": "ratio",
        "direction": "higher",
        "rank": True,
        "sources": ["ine-defunciones-2025", "ine-nacimientos-2025"],
        "license_summary": "INE, estadísticas públicas.",
        "description": (
            "Defunciones de residentes menores de 5 años por 1,000 nacimientos "
            "de residentes en 2025. Se suprime cuando el conteo es menor que 5."
        ),
    },
    {
        "key": "pobreza_general_pct_2023",
        "label": "Pobreza general municipal 2023",
        "short_label": "Pobreza general",
        "unit": "%",
        "format": "percent",
        "direction": "higher",
        "rank": True,
        "sources": ["segeplan-pobreza-2023"],
        "license_summary": "SEGEPLAN CC BY-NC 2.0 (uso no comercial).",
        "description": "Incidencia de pobreza general estimada por SEGEPLAN para 2023.",
    },
    {
        "key": "asignacion_por_habitante_2026_gtq",
        "label": "Asignación constitucional por habitante 2026",
        "short_label": "Asignación por habitante",
        "unit": "Q por habitante",
        "format": "currency",
        "direction": "lower",
        "rank": True,
        "sources": ["segeplan-asignacion-2026"],
        "license_summary": "SEGEPLAN CC BY-NC 2.0 (uso no comercial).",
        "description": (
            "Situado constitucional 2026 dividido por la población usada por "
            "SEGEPLAN. Un valor menor indica más presión relativa."
        ),
    },
    {
        "key": "crecimiento_abs_2025_2035",
        "label": "Crecimiento absoluto 2025–2035",
        "short_label": "Crecimiento absoluto",
        "unit": "personas",
        "format": "integer",
        "direction": None,
        "rank": False,
        "sources": ["ine-proyecciones-2035"],
        "license_summary": "INE, estadísticas públicas.",
        "description": "Diferencia en personas entre la población proyectada de 2035 y 2025.",
    },
    {
        "key": "poblacion_2025",
        "label": "Población proyectada 2025",
        "short_label": "Población 2025",
        "unit": "personas",
        "format": "integer",
        "direction": None,
        "rank": False,
        "sources": ["ine-proyecciones-2035"],
        "license_summary": "INE, estadísticas públicas.",
        "description": "Población total municipal proyectada al 30 de junio de 2025.",
    },
]


PRESSURE_INDICATOR_KEYS = [
    "crecimiento_poblacional_pct",
    "nacimientos_por_escuela_2025",
    "asignacion_presion_indice_2026",
]

PRESSURE_CLASS_LABELS = {
    "alta": "Presión alta",
    "media_alta": "Presión media-alta",
    "media": "Presión media",
    "baja": "Presión baja",
    "sin_dato": "Sin dato",
}


def _safe_divide(
    numerator: pd.Series, denominator: pd.Series, factor: float = 1.0
) -> pd.Series:
    result = numerator.astype("Float64") / denominator.replace({0: pd.NA}).astype(
        "Float64"
    )
    return (result * factor).astype("Float64")


def _pressure_class(percentile: float | None) -> str:
    if percentile is None or pd.isna(percentile):
        return "sin_dato"
    if percentile >= 75:
        return "alta"
    if percentile >= 50:
        return "media_alta"
    if percentile >= 25:
        return "media"
    return "baja"


def _join(left: pd.DataFrame, right: pd.DataFrame, name: str) -> pd.DataFrame:
    if right["codigo"].duplicated().any():
        duplicates = right.loc[right["codigo"].duplicated(), "codigo"].tolist()[:10]
        raise ValueError(f"El cruce con {name} tiene códigos duplicados: {duplicates}")
    merged = left.merge(right, on="codigo", how="left", validate="one_to_one")
    if len(merged) != 340:
        raise ValueError(
            f"El cruce con {name} cambió el número de filas a {len(merged)}"
        )
    missing = merged["codigo"].isna().sum()
    if missing:
        raise ValueError(f"El cruce con {name} dejó {missing} códigos sin municipio")
    return merged


def build_indicators(
    reference: pd.DataFrame,
    projection_2035: pd.DataFrame,
    projection_2030: pd.DataFrame,
    births: pd.DataFrame,
    deaths: pd.DataFrame,
    establishments: pd.DataFrame,
    students: pd.DataFrame,
    poverty: pd.DataFrame,
    allocation: pd.DataFrame,
) -> tuple[pd.DataFrame, dict]:
    """Join every source to the 340-municipality catalogue and compute indicators."""

    frame = reference.rename(columns={"municipio_codigo": "codigo"}).copy()
    assert_unique_codes(frame["codigo"], "catálogo de indicadores")

    projection_columns = [
        "codigo",
        "poblacion_2015",
        "poblacion_2025",
        "poblacion_2030",
        "poblacion_2035",
    ]
    frame = _join(frame, projection_2035[projection_columns], "proyecciones 2015-2035")
    frame = _join(
        frame,
        projection_2030[["codigo", "poblacion_2030"]].rename(
            columns={"poblacion_2030": "poblacion_2030_ckan"}
        ),
        "proyecciones 2015-2030",
    )
    frame = _join(frame, births, "nacimientos 2025")
    frame = _join(frame, deaths, "defunciones 2025")
    frame = _join(frame, establishments, "establecimientos MINEDUC")
    frame = _join(frame, students, "estudiantes MINEDUC")
    frame = _join(
        frame,
        poverty[
            [
                "codigo",
                "pobreza_general_pct_2023",
                "pobreza_extrema_pct_2023",
                "poblacion_en_pobreza_2023",
                "poblacion_en_pobreza_extrema_2023",
                "brecha_pobreza_general_2023",
                "severidad_pobreza_general_2023",
                "consumo_promedio_q_mes_2023",
            ]
        ],
        "pobreza SEGEPLAN",
    )
    frame = _join(
        frame,
        allocation[
            [
                "codigo",
                "asignacion_constitucional_2026_gtq",
                "poblacion_asignacion_2025",
                "asignacion_por_habitante_2026_gtq",
                "ingresos_propios_2024_gtq",
                "ingresos_propios_per_capita_2024_gtq",
                "aldeas_caserios_2025",
            ]
        ],
        "asignación SEGEPLAN",
    )

    if frame["codigo"].nunique() != 340 or len(frame) != 340:
        raise ValueError("La tabla de indicadores no tiene 340 municipios únicos")

    # --- demographic change -------------------------------------------------
    frame["crecimiento_abs_2025_2035"] = (
        frame["poblacion_2035"] - frame["poblacion_2025"]
    ).astype("Int64")
    frame["crecimiento_poblacional_pct"] = _safe_divide(
        frame["crecimiento_abs_2025_2035"].astype("Float64"),
        frame["poblacion_2025"],
        100.0,
    )
    frame["crecimiento_poblacional_pct_2015_2025"] = _safe_divide(
        frame["poblacion_2025"] - frame["poblacion_2015"],
        frame["poblacion_2015"],
        100.0,
    )

    # --- vital events -------------------------------------------------------
    births_series = frame["nacimientos_2025"].astype("Float64")
    deaths_series = frame["defunciones_2025"].astype("Float64")
    population_series = frame["poblacion_2025"].astype("Float64")
    frame["nacimientos_por_1000_habitantes_2025"] = _safe_divide(
        births_series, population_series, 1000.0
    )
    frame["tasa_mortalidad_general_2025"] = _safe_divide(
        deaths_series, population_series, 1000.0
    )
    frame["tasa_mortalidad_menor_5_2025"] = _safe_divide(
        frame["defunciones_menores_5_2025"].astype("Float64"),
        births_series,
        1000.0,
    )
    frame["relacion_nacimientos_defunciones_2025"] = _safe_divide(
        births_series, deaths_series
    )

    # --- school supply and load --------------------------------------------
    schools = frame["escuelas_2022"].astype("Float64")
    students_series = frame["estudiantes_2022"].astype("Float64")
    frame["nacimientos_por_escuela_2025"] = _safe_divide(births_series, schools)
    frame["estudiantes_por_escuela_2022"] = _safe_divide(students_series, schools)
    frame["nacimientos_por_100_estudiantes_2025"] = _safe_divide(
        births_series, students_series, 100.0
    )
    frame["escuelas_por_10000_habitantes_2022"] = _safe_divide(
        schools,
        frame["poblacion_2025"].astype("Float64"),
        10000.0,
    )
    frame["estudiantes_por_10000_habitantes_2022"] = _safe_divide(
        students_series,
        frame["poblacion_2025"].astype("Float64"),
        10000.0,
    )

    # --- fiscal pressure ----------------------------------------------------
    national_per_capita = (
        frame["asignacion_constitucional_2026_gtq"].sum()
        / frame["poblacion_asignacion_2025"].sum()
    )
    frame["asignacion_presion_indice_2026"] = (
        national_per_capita / frame["asignacion_por_habitante_2026_gtq"]
    ).astype("Float64")

    # --- suppression --------------------------------------------------------
    frame, count_summary = suppress_counts(frame)
    frame, derived_summary = suppress_derived(frame)

    # --- relative pressure scores ------------------------------------------
    pressure: dict[str, dict] = {}
    for definition in INDICATOR_DEFINITIONS:
        key = definition["key"]
        if not definition.get("rank") or key not in frame.columns:
            continue
        values = pd.to_numeric(frame[key], errors="coerce")
        direction = definition["direction"]
        ascending = direction == "higher"
        percentile = values.rank(pct=True, method="average", ascending=ascending) * 100
        national_rank = values.rank(method="min", ascending=not ascending)
        department_rank = values.groupby(frame["departamento_codigo"]).rank(
            method="min", ascending=not ascending
        )
        pressure[key] = {
            "percentil_nacional": percentile,
            "rank_nacional": national_rank,
            "rank_departamento": department_rank,
        }

    for definition in INDICATOR_DEFINITIONS:
        key = definition["key"]
        if key not in pressure:
            continue
        frame[f"{key}_percentil"] = pressure[key]["percentil_nacional"].astype(
            "Float64"
        )
        frame[f"{key}_rank_nacional"] = pressure[key]["rank_nacional"].astype("Int64")
        frame[f"{key}_rank_departamento"] = pressure[key]["rank_departamento"].astype(
            "Int64"
        )
        frame[f"{key}_clase"] = pressure[key]["percentil_nacional"].map(_pressure_class)

    # A compact classification used by the UI when it needs one label.
    frame["presion_crecimiento_clase"] = frame["crecimiento_poblacional_pct_clase"]
    frame["presion_escuela_clase"] = frame["nacimientos_por_escuela_2025_clase"]
    frame["presion_asignacion_clase"] = frame["asignacion_presion_indice_2026_clase"]

    # Publish counts and population as nullable integers, not floats. This keeps
    # the JSON clean and makes "suppressed" (null) distinct from a numeric zero.
    integer_columns = [
        "poblacion_2015",
        "poblacion_2025",
        "poblacion_2030",
        "poblacion_2030_ckan",
        "poblacion_2035",
        "crecimiento_abs_2025_2035",
        "nacimientos_2025",
        "defunciones_2025",
        "defunciones_menores_5_2025",
        "escuelas_2022",
        "escuelas_publicas_2022",
        "estudiantes_2022",
        "estudiantes_publicos_2022",
        "poblacion_en_pobreza_2023",
        "poblacion_en_pobreza_extrema_2023",
        "poblacion_asignacion_2025",
        "aldeas_caserios_2025",
    ]
    for column in integer_columns:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce").astype(
                "Int64"
            )

    # --- metadata -----------------------------------------------------------
    class_counts = {
        key: {
            label: int((frame[f"{key}_clase"] == code).sum())
            for code, label in PRESSURE_CLASS_LABELS.items()
        }
        for key in PRESSURE_INDICATOR_KEYS
    }
    complete_pressure = frame[PRESSURE_INDICATOR_KEYS].notna().all(axis=1).sum()
    metadata = {
        "municipalities": int(len(frame)),
        "departments": int(frame["departamento_codigo"].nunique()),
        "national_per_capita_allocation_2026_gtq": float(national_per_capita),
        "pressure_classes": class_counts,
        "municipalities_with_complete_pressure": int(complete_pressure),
        "missing_extreme_poverty": int(frame["pobreza_extrema_pct_2023"].isna().sum()),
        "suppression": {
            "counts": count_summary,
            "derived": derived_summary,
            "total_suppressed_cells": (
                count_summary["suppressed_cells_total"]
                + derived_summary["suppressed_cells_total"]
            ),
        },
        "national_totals": {
            "poblacion_2025": int(frame["poblacion_2025"].sum()),
            "poblacion_2035": int(frame["poblacion_2035"].sum()),
            "nacimientos_2025": int(frame["nacimientos_2025"].sum()),
            "defunciones_2025": int(frame["defunciones_2025"].sum()),
            "escuelas_2022": int(frame["escuelas_2022"].sum()),
            "estudiantes_2022": int(frame["estudiantes_2022"].sum()),
            "asignacion_constitucional_2026_gtq": float(
                frame["asignacion_constitucional_2026_gtq"].sum()
            ),
        },
        "definitions": INDICATOR_DEFINITIONS,
        "suppression_labels": {
            **COUNT_LABELS,
            **DERIVED_LABELS,
        },
    }
    return frame.rename(columns={"codigo": "municipio_codigo"}).sort_values(
        "municipio_codigo"
    ).reset_index(drop=True), metadata
