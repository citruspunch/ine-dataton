"""Aggregate MINEDUC school and enrolment files to municipality level.

The public MINEDUC portal (CKAN, CC0) publishes the 2021-2022 school directory
and enrolment by municipality. The latest cycle is 2022, so school supply is a
2022 snapshot compared with 2025 births; this mismatch is stated in the UI and
README.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .normalize import normalize_department_code, normalize_municipio_code


LATEST_SCHOOL_YEAR = "2022"


def _code(department: object, municipality: object) -> str:
    dept = normalize_department_code(department)
    muni = normalize_municipio_code(municipality)
    return f"{dept}{muni[2:]}"


def load_establishments(
    path: Path, reference_codes: set[str]
) -> tuple[pd.DataFrame, dict]:
    raw = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
    required = {"CodDepartamento", "CodMuni", "CodigoEst", "Año", "Sector"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"Establecimientos MINEDUC: faltan columnas {sorted(missing)}")
    raw["Año"] = raw["Año"].fillna("").astype(str)
    current = raw[raw["Año"].str.startswith(LATEST_SCHOOL_YEAR)].copy()
    if current.empty:
        raise ValueError("Establecimientos MINEDUC: no hay filas para 2022")

    current["codigo"] = [
        _code(department, municipality)
        for department, municipality in zip(
            current["CodDepartamento"], current["CodMuni"]
        )
    ]
    outside = current[~current["codigo"].isin(reference_codes)]
    valid = current[current["codigo"].isin(reference_codes)]

    schools = valid.groupby("codigo")["CodigoEst"].nunique().rename("escuelas_2022")
    public = (
        valid[valid["Sector"].str.upper().str.strip() == "OFICIAL"]
        .groupby("codigo")["CodigoEst"]
        .nunique()
        .rename("escuelas_publicas_2022")
    )
    frame = pd.concat([schools, public], axis=1).reindex(sorted(reference_codes))
    frame = frame.fillna(0).astype("int64").reset_index()
    frame.columns = ["codigo", "escuelas_2022", "escuelas_publicas_2022"]

    meta = {
        "rows_total": int(len(raw)),
        "rows_year_2022": int(len(current)),
        "rows_used": int(len(valid)),
        "rows_outside_catalog": int(len(outside)),
        "municipalities_with_data": int((frame["escuelas_2022"] > 0).sum()),
        "zero_filled_municipalities": int((frame["escuelas_2022"] == 0).sum()),
        "total_schools": int(frame["escuelas_2022"].sum()),
        "total_public_schools": int(frame["escuelas_publicas_2022"].sum()),
        "min_schools": int(frame["escuelas_2022"].min()),
        "max_schools": int(frame["escuelas_2022"].max()),
        "min_public_schools": int(frame["escuelas_publicas_2022"].min()),
        "year": LATEST_SCHOOL_YEAR,
        "counting_rule": "Conteo de CodigoEst únicos por municipio y ciclo 2022.",
    }
    return frame, meta


def load_students(path: Path, reference_codes: set[str]) -> tuple[pd.DataFrame, dict]:
    raw = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
    required = {"CodDep", "CodMun", "Año", "InscritosTotal", "Sector"}
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(f"Estudiantes MINEDUC: faltan columnas {sorted(missing)}")
    raw["Año"] = raw["Año"].fillna("").astype(str)
    current = raw[raw["Año"].str.startswith(LATEST_SCHOOL_YEAR)].copy()
    if current.empty:
        raise ValueError("Estudiantes MINEDUC: no hay filas para 2022")

    current["codigo"] = [
        _code(department, municipality)
        for department, municipality in zip(current["CodDep"], current["CodMun"])
    ]
    current["inscritos"] = pd.to_numeric(
        current["InscritosTotal"], errors="coerce"
    ).fillna(0)
    current["inscritos_publicos"] = current["inscritos"].where(
        current["Sector"].str.upper().str.strip() == "OFICIAL", 0
    )
    outside = current[~current["codigo"].isin(reference_codes)]
    valid = current[current["codigo"].isin(reference_codes)]

    students = valid.groupby("codigo")["inscritos"].sum().rename("estudiantes_2022")
    public = (
        valid.groupby("codigo")["inscritos_publicos"]
        .sum()
        .rename("estudiantes_publicos_2022")
    )
    frame = pd.concat([students, public], axis=1).reindex(sorted(reference_codes))
    frame = frame.fillna(0).astype("int64").reset_index()
    frame.columns = ["codigo", "estudiantes_2022", "estudiantes_publicos_2022"]

    meta = {
        "rows_total": int(len(raw)),
        "rows_year_2022": int(len(current)),
        "rows_used": int(len(valid)),
        "rows_outside_catalog": int(len(outside)),
        "municipalities_with_data": int((frame["estudiantes_2022"] > 0).sum()),
        "zero_filled_municipalities": int((frame["estudiantes_2022"] == 0).sum()),
        "total_students": int(frame["estudiantes_2022"].sum()),
        "total_public_students": int(frame["estudiantes_publicos_2022"].sum()),
        "min_students": int(frame["estudiantes_2022"].min()),
        "max_students": int(frame["estudiantes_2022"].max()),
        "year": LATEST_SCHOOL_YEAR,
        "counting_rule": "Suma de InscritosTotal por municipio y ciclo 2022.",
    }
    return frame, meta
