"""SEGEPLAN municipal poverty and constitutional-allocation files.

Both datasets are published with CKAN license ``cc-nc`` (CC BY-NC 2.0). The
pipeline keeps that fact attached to the data and the UI repeats the
non-commercial notice wherever these indicators appear.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from .normalize import normalize_municipio_code


def parse_number(value: object) -> float:
    """Parse ``Q1,234.56``, ``1,234``, ``'4.4'`` and ``'Q-'``."""

    if value is None:
        return float("nan")
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)
    text = str(value).strip()
    if text in {"", "-", "--", "Q-", "N/A", "n.d.", "nan", "NaN"}:
        return float("nan")
    negative = text.startswith("(") and text.endswith(")")
    cleaned = re.sub(r"[^0-9,.\-]", "", text)
    if cleaned in {"", "-", ".", "-."}:
        return float("nan")
    cleaned = cleaned.replace(",", "")
    try:
        number = float(cleaned)
    except ValueError:
        return float("nan")
    return -number if negative else number


def _rename_poverty(columns: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for column in columns:
        compact = re.sub(r"\s+", " ", column.replace("\n", " ")).strip()
        if compact == "Codigo":
            mapping[column] = "codigo"
        elif compact == "Departamento":
            mapping[column] = "departamento_segeplan"
        elif compact == "Municipio":
            mapping[column] = "municipio_segeplan"
        elif compact == "Poblacion total":
            mapping[column] = "poblacion_pobreza_2023"
        elif compact == "Poblacion en condicion de pobreza":
            mapping[column] = "poblacion_en_pobreza_2023"
        elif compact == "Incidencia de pobreza general":
            mapping[column] = "pobreza_general_pct_2023"
        elif compact == "Incidencia de pobreza extrema":
            mapping[column] = "pobreza_extrema_pct_2023"
        elif compact == "Brecha de pobreza general":
            mapping[column] = "brecha_pobreza_general_2023"
        elif compact == "Severidad de pobreza general":
            mapping[column] = "severidad_pobreza_general_2023"
        elif compact.startswith("Consumo promedio en Q/mes"):
            mapping[column] = "consumo_promedio_q_mes_2023"
        elif compact.startswith("Poblacion en condicion de pobreza extrema"):
            mapping[column] = "poblacion_en_pobreza_extrema_2023"
    return mapping


def load_poverty(path: Path, reference_codes: set[str]) -> tuple[pd.DataFrame, dict]:
    raw = pd.read_csv(path, sep=";", encoding="utf-8-sig", dtype=str)
    raw = raw.rename(columns=_rename_poverty(list(raw.columns)))
    required = {
        "codigo",
        "departamento_segeplan",
        "municipio_segeplan",
        "pobreza_general_pct_2023",
    }
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"Pobreza SEGEPLAN: faltan columnas {sorted(missing)}")

    frame = raw.copy()
    frame["codigo"] = frame["codigo"].map(normalize_municipio_code)
    for column in [
        "poblacion_pobreza_2023",
        "poblacion_en_pobreza_2023",
        "pobreza_general_pct_2023",
        "pobreza_extrema_pct_2023",
        "brecha_pobreza_general_2023",
        "severidad_pobreza_general_2023",
        "consumo_promedio_q_mes_2023",
        "poblacion_en_pobreza_extrema_2023",
    ]:
        if column not in frame.columns:
            frame[column] = np.nan
        frame[column] = frame[column].map(parse_number)

    outside = frame[~frame["codigo"].isin(reference_codes)]
    if len(outside):
        raise ValueError(
            "Pobreza SEGEPLAN: códigos fuera del catálogo "
            f"{outside['codigo'].tolist()[:10]}"
        )
    if frame["codigo"].duplicated().any():
        raise ValueError("Pobreza SEGEPLAN: códigos duplicados")
    if len(frame) != 340:
        raise ValueError(f"Pobreza SEGEPLAN: se esperaban 340 filas, hay {len(frame)}")

    frame = frame.sort_values("codigo").reset_index(drop=True)
    missing_extreme = int(frame["pobreza_extrema_pct_2023"].isna().sum())
    meta = {
        "rows": int(len(frame)),
        "municipalities": int(frame["codigo"].nunique()),
        "missing_extreme_poverty": missing_extreme,
        "national_general_poverty_mean_unweighted": float(
            frame["pobreza_general_pct_2023"].mean()
        ),
        "national_extreme_poverty_mean_unweighted": float(
            frame["pobreza_extrema_pct_2023"].mean()
        )
        if frame["pobreza_extrema_pct_2023"].notna().any()
        else None,
        "year": 2023,
        "notes": (
            "La incidencia de pobreza extrema no está publicada para "
            f"{missing_extreme} municipios; se muestra como no disponible."
        ),
    }
    return frame, meta


def load_allocation(path: Path, reference_codes: set[str]) -> tuple[pd.DataFrame, dict]:
    raw = pd.read_csv(path, sep=";", encoding="latin-1", dtype=str)
    raw.columns = [column.replace("\ufeff", "").strip() for column in raw.columns]
    mapping = {
        "Código de municipio": "codigo",
        "Municipios b/": "municipio_segeplan",
        "Depto.": "departamento_iso_segeplan",
        "TOTAL GENERAL": "asignacion_constitucional_2026_gtq",
        "Población total 2025c/": "poblacion_asignacion_2025",
        "Ingresos Propios 2024 SIAF-CGC d/": "ingresos_propios_2024_gtq",
        "No. de Aldeas y Caserios 2025e/": "aldeas_caserios_2025",
        "Ingresos Propios Per Cápita": "ingresos_propios_per_capita_2024_gtq",
    }
    raw = raw.rename(columns=mapping)
    required = {"codigo", "asignacion_constitucional_2026_gtq"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"Asignación SEGEPLAN: faltan columnas {sorted(missing)}")

    frame = raw[raw["codigo"].notna()].copy()
    frame["codigo"] = frame["codigo"].map(
        lambda value: (
            normalize_municipio_code(value)
            if str(value).strip() not in {"", "nan"}
            else None
        )
    )
    frame = frame[frame["codigo"].notna()].copy()
    for column in [
        "asignacion_constitucional_2026_gtq",
        "poblacion_asignacion_2025",
        "ingresos_propios_2024_gtq",
        "aldeas_caserios_2025",
        "ingresos_propios_per_capita_2024_gtq",
    ]:
        if column not in frame.columns:
            frame[column] = np.nan
        frame[column] = frame[column].map(parse_number)

    outside = frame[~frame["codigo"].isin(reference_codes)]
    if len(outside):
        raise ValueError(
            "Asignación SEGEPLAN: códigos fuera del catálogo "
            f"{outside['codigo'].tolist()[:10]}"
        )
    if frame["codigo"].duplicated().any():
        raise ValueError("Asignación SEGEPLAN: códigos duplicados")
    if len(frame) != 340:
        raise ValueError(
            f"Asignación SEGEPLAN: se esperaban 340 filas, hay {len(frame)}"
        )

    frame["asignacion_por_habitante_2026_gtq"] = (
        frame["asignacion_constitucional_2026_gtq"] / frame["poblacion_asignacion_2025"]
    )
    frame = frame.sort_values("codigo").reset_index(drop=True)
    meta = {
        "rows": int(len(frame)),
        "municipalities": int(frame["codigo"].nunique()),
        "total_allocation_gtq": float(
            frame["asignacion_constitucional_2026_gtq"].sum()
        ),
        "national_per_capita_gtq": float(
            frame["asignacion_constitucional_2026_gtq"].sum()
            / frame["poblacion_asignacion_2025"].sum()
        ),
        "year": 2026,
        "notes": (
            "Cálculo matemático del situado constitucional 2026. No es ejecución "
            "presupuestaria; la población de referencia es la usada por SEGEPLAN "
            "en el cálculo (2025)."
        ),
    }
    return frame, meta
