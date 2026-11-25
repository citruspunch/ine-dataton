"""Aggregate 2025 births and deaths to the 340-municipality grid.

Births are assigned to the mother's municipality of residence
(``Deprem``/``Muprem``). Deaths are assigned to the deceased's municipality of
residence (``Dredif``/``MreDif``). Codes outside the 340-municipality catalogue
(``2300``, ``9999`` and similar) are excluded and counted in the metadata rather
than silently dropped.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .normalize import normalize_department_code, normalize_municipio_code


YEAR = 2025


def _municipal_code(department: object, municipality: object) -> str | None:
    try:
        dept = normalize_department_code(department)
        muni = normalize_municipio_code(municipality)
    except ValueError:
        return None
    return f"{dept}{muni[2:]}"


def _unmatched_summary(codes: pd.Series, reference_codes: set[str]) -> list[dict]:
    outside = codes[~codes.isin(reference_codes)]
    if outside.empty:
        return []
    counts = outside.value_counts().head(10)
    return [
        {"codigo": str(code), "registros": int(count)} for code, count in counts.items()
    ]


def load_births(path: Path, reference_codes: set[str]) -> tuple[pd.DataFrame, dict]:
    raw = pd.read_excel(
        path,
        usecols=["Deprem", "Muprem", "Añoreg"],
        dtype={"Deprem": str, "Muprem": str},
    )
    raw["Añoreg"] = pd.to_numeric(raw["Añoreg"], errors="coerce")
    rows_total = len(raw)
    current = raw[raw["Añoreg"] == YEAR].copy()
    current["codigo"] = [
        _municipal_code(department, municipality)
        for department, municipality in zip(current["Deprem"], current["Muprem"])
    ]
    valid = current[current["codigo"].notna() & current["codigo"].isin(reference_codes)]
    unmatched = current[
        current["codigo"].isna() | ~current["codigo"].isin(reference_codes)
    ]

    counts = valid.groupby("codigo").size().rename("nacimientos_2025")
    frame = counts.reindex(sorted(reference_codes), fill_value=0).reset_index()
    frame.columns = ["codigo", "nacimientos_2025"]
    frame["nacimientos_2025"] = frame["nacimientos_2025"].astype("int64")

    meta = {
        "rows_total": int(rows_total),
        "rows_year_2025": int(len(current)),
        "rows_used": int(len(valid)),
        "rows_unmatched": int(len(unmatched)),
        "unmatched_codes": _unmatched_summary(
            current["codigo"].dropna(), reference_codes
        ),
        "municipalities_with_data": int((frame["nacimientos_2025"] > 0).sum()),
        "zero_filled_municipalities": int((frame["nacimientos_2025"] == 0).sum()),
        "total_used": int(frame["nacimientos_2025"].sum()),
        "residence_field": "Deprem + Muprem (residencia de la madre)",
        "year_field": "Añoreg = 2025",
        "min_count": int(frame["nacimientos_2025"].min()),
        "max_count": int(frame["nacimientos_2025"].max()),
    }
    return frame, meta


def load_deaths(path: Path, reference_codes: set[str]) -> tuple[pd.DataFrame, dict]:
    raw = pd.read_excel(
        path,
        usecols=["Dredif", "MreDif", "Añoreg", "Edadif"],
        dtype={"Dredif": str, "MreDif": str},
    )
    raw["Añoreg"] = pd.to_numeric(raw["Añoreg"], errors="coerce")
    raw["Edadif"] = pd.to_numeric(raw["Edadif"], errors="coerce")
    rows_total = len(raw)
    current = raw[raw["Añoreg"] == YEAR].copy()
    current["codigo"] = [
        _municipal_code(department, municipality)
        for department, municipality in zip(current["Dredif"], current["MreDif"])
    ]
    valid = current[current["codigo"].notna() & current["codigo"].isin(reference_codes)]
    unmatched = current[
        current["codigo"].isna() | ~current["codigo"].isin(reference_codes)
    ]

    total = valid.groupby("codigo").size().rename("defunciones_2025")
    under5 = (
        valid[valid["Edadif"] < 5]
        .groupby("codigo")
        .size()
        .rename("defunciones_menores_5_2025")
    )
    frame = pd.concat([total, under5], axis=1).reindex(sorted(reference_codes))
    frame = frame.fillna(0).astype("int64").reset_index()
    frame.columns = ["codigo", "defunciones_2025", "defunciones_menores_5_2025"]

    meta = {
        "rows_total": int(rows_total),
        "rows_year_2025": int(len(current)),
        "rows_used": int(len(valid)),
        "rows_unmatched": int(len(unmatched)),
        "unmatched_codes": _unmatched_summary(
            current["codigo"].dropna(), reference_codes
        ),
        "municipalities_with_data": int((frame["defunciones_2025"] > 0).sum()),
        "zero_filled_municipalities": int((frame["defunciones_2025"] == 0).sum()),
        "total_used": int(frame["defunciones_2025"].sum()),
        "under5_total": int(frame["defunciones_menores_5_2025"].sum()),
        "under5_min": int(frame["defunciones_menores_5_2025"].min()),
        "under5_max": int(frame["defunciones_menores_5_2025"].max()),
        "under5_municipalities_with_data": int(
            (frame["defunciones_menores_5_2025"] > 0).sum()
        ),
        "under5_small_count_candidates": int(
            (
                (frame["defunciones_menores_5_2025"] > 0)
                & (frame["defunciones_menores_5_2025"] < 5)
            ).sum()
        ),
        "residence_field": "Dredif + MreDif (residencia del fallecido)",
        "under5_definition": "Edadif < 5 años",
        "year_field": "Añoreg = 2025",
    }
    return frame, meta
