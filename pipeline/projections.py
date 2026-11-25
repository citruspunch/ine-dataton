"""Read and normalise the two INE municipal projection vintages."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .normalize import (
    apply_guatemala_crosswalk,
    assert_unique_codes,
    normalize_municipio_code,
)


PROJECTION_YEARS_2035 = list(range(2015, 2036))
PROJECTION_YEARS_2030 = list(range(2015, 2031))


def load_projection_2035(path: Path) -> tuple[pd.DataFrame, dict]:
    """Parse the wide 2015-2035 municipal table (one row per municipality)."""

    raw = pd.read_excel(path, header=None)
    header_row = None
    for index in range(min(20, len(raw))):
        values = {
            int(v)
            for v in raw.iloc[index].tolist()
            if isinstance(v, (int, float)) and not pd.isna(v)
        }
        if 2015 in values and 2035 in values:
            header_row = index
            break
    if header_row is None:
        raise ValueError("No se encontró la fila de encabezado 2015-2035")

    rows: list[dict] = []
    department: tuple[str, str] | None = None
    for _, row in raw.iloc[header_row + 1 :].iterrows():
        code_value = row.iloc[0]
        name_value = row.iloc[1]
        if pd.isna(code_value) or pd.isna(name_value):
            continue
        try:
            numeric_code = int(float(code_value))
        except (TypeError, ValueError):
            continue
        if numeric_code < 100:
            department = (f"{numeric_code:02d}", str(name_value).strip())
            continue
        if department is None:
            raise ValueError(
                f"Municipio sin departamento: {code_value!r} {name_value!r}"
            )
        record = {
            "codigo": normalize_municipio_code(numeric_code),
            "codigo_fuente": str(numeric_code),
            "municipio_nombre": str(name_value).strip(),
            "departamento_codigo": department[0],
            "departamento_nombre": department[1],
        }
        for offset, year in enumerate(PROJECTION_YEARS_2035, start=2):
            record[f"poblacion_{year}"] = pd.to_numeric(
                row.iloc[offset], errors="coerce"
            )
        rows.append(record)

    frame = pd.DataFrame(rows)
    if frame.empty:
        raise ValueError("La proyección 2015-2035 no produjo filas municipales")
    assert_unique_codes(frame["codigo"], "proyección 2015-2035")
    if frame["departamento_codigo"].nunique() != 22:
        raise ValueError(
            f"Se esperaban 22 departamentos, hay {frame['departamento_codigo'].nunique()}"
        )
    frame = frame.sort_values("codigo").reset_index(drop=True)
    meta = {
        "rows": int(len(frame)),
        "departments": int(frame["departamento_codigo"].nunique()),
        "years": [2015, 2035],
        "coding_note": (
            "La tabla ancha usa códigos como 101 y 2217; se normalizan a 0101 y 2217."
        ),
    }
    return frame, meta


def load_projection_2030(path: Path) -> tuple[pd.DataFrame, dict]:
    """Parse the long 2015-2030 table and apply the Guatemala +21 crosswalk."""

    raw = pd.read_excel(path, dtype={"DEPTO": str, "MUPIO": str})
    missing_years = [year for year in PROJECTION_YEARS_2030 if year not in raw.columns]
    if missing_years:
        raise ValueError(f"Faltan años en la proyección 2015-2030: {missing_years}")
    raw[PROJECTION_YEARS_2030] = raw[PROJECTION_YEARS_2030].apply(
        pd.to_numeric, errors="coerce"
    )

    # SEXO 0 is the total, 1 and 2 are the sex breakdowns. Summing all three
    # would double-count the population (a failure mode caught by the overlap
    # check against the wide 2015-2035 table).
    totals = raw[raw["SEXO"].astype(str).str.strip() == "0"].copy()
    if totals.empty:
        raise ValueError("La proyección 2015-2030 no contiene filas SEXO=0 (total)")

    grouped = (
        totals.groupby(["DEPTO", "MUPIO"], as_index=False)[PROJECTION_YEARS_2030]
        .sum()
        .reset_index(drop=True)
    )

    codes: list[str] = []
    applied: list[bool] = []
    for department, municipality in zip(grouped["DEPTO"], grouped["MUPIO"]):
        code, was_applied = apply_guatemala_crosswalk(department, municipality)
        codes.append(code)
        applied.append(was_applied)
    grouped["codigo"] = codes
    grouped["crosswalk_aplicado"] = applied

    assert_unique_codes(grouped["codigo"], "proyección 2015-2030")
    crosswalk_count = int(grouped["crosswalk_aplicado"].sum())
    if crosswalk_count != 16:
        raise ValueError(
            f"El cruce +21 debía aplicarse a 16 municipios de Guatemala, se aplicó a {crosswalk_count}"
        )

    grouped = grouped.rename(
        columns={year: f"poblacion_{year}" for year in PROJECTION_YEARS_2030}
    )
    keep = ["codigo", "crosswalk_aplicado"] + [
        f"poblacion_{year}" for year in PROJECTION_YEARS_2030
    ]
    grouped = grouped[keep].sort_values("codigo").reset_index(drop=True)
    meta = {
        "rows": int(len(grouped)),
        "raw_rows": int(len(raw)),
        "crosswalk_applied": crosswalk_count,
        "crosswalk_mapping": "0123-0138 -> 0102-0117 (restar 21 al correlativo municipal)",
        "sex_filter": "SEXO=0 (total); se excluyen las filas de sexo 1 y 2 para no duplicar la población",
        "years": [2015, 2030],
    }
    return grouped, meta


def build_reference_catalog(projection_2035: pd.DataFrame) -> pd.DataFrame:
    """The application's 340-municipality reference catalogue."""

    catalog = projection_2035[
        [
            "codigo",
            "municipio_nombre",
            "departamento_codigo",
            "departamento_nombre",
        ]
    ].copy()
    catalog = catalog.rename(columns={"codigo": "municipio_codigo"})
    assert_unique_codes(catalog["municipio_codigo"], "catálogo de referencia")
    catalog = catalog.sort_values("municipio_codigo").reset_index(drop=True)
    return catalog


def validate_overlap(
    projection_2035: pd.DataFrame,
    projection_2030: pd.DataFrame,
    tolerance_people: float = 1.0,
) -> dict:
    """Compare the two vintages on 2015-2030; record, do not hide, differences."""

    merged = projection_2035.merge(
        projection_2030, on="codigo", suffixes=("_2035", "_2030"), how="inner"
    )
    if len(merged) != 340:
        raise ValueError(
            f"El traslape de proyecciones tiene {len(merged)} filas, no 340"
        )

    differences: dict[str, float] = {}
    for year in PROJECTION_YEARS_2030:
        left = pd.to_numeric(merged[f"poblacion_{year}_2035"], errors="coerce")
        right = pd.to_numeric(merged[f"poblacion_{year}_2030"], errors="coerce")
        differences[str(year)] = float((left - right).abs().max())

    worst_year = max(differences, key=differences.get)
    worst = differences[worst_year]
    if worst > tolerance_people:
        raise ValueError(
            "Las proyecciones 2015-2030 y 2015-2035 no coinciden en el traslape: "
            f"máxima diferencia {worst:.0f} personas en {worst_year}."
        )
    return {
        "rows_compared": int(len(merged)),
        "years": [2015, 2030],
        "max_abs_difference_people": worst,
        "max_abs_difference_year": int(worst_year),
        "by_year": differences,
        "tolerance_people": tolerance_people,
        "status": "ok",
    }


def projection_long_codes(projection_2030: pd.DataFrame) -> set[str]:
    return set(projection_2030["codigo"].astype(str))


def projection_wide_codes(projection_2035: pd.DataFrame) -> set[str]:
    return set(projection_2035["codigo"].astype(str))
