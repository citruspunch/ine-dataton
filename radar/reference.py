"""Load the census, projection, populated-place and boundary references."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .config import DEPARTMENT_NAMES, POPULATION_YEAR
from .normalize import (
    canonical_municipality,
    crosswalk_census_to_projection,
    normalize_municipality,
    valid_department,
)


def load_crosswalk(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype=str)
    required = {"code", "name", "dept_code", "dept_name", "census_code", "geo_shape_id"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Faltan columnas en {path}: {sorted(missing)}")
    frame["code"] = frame["code"].str.zfill(4)
    frame["census_code"] = frame["census_code"].str.zfill(4)
    frame["dept_code"] = frame["code"].str[:2]
    if frame["code"].nunique() != 340:
        raise ValueError(
            f"El cruce municipal debe tener 340 códigos, no {frame['code'].nunique()}."
        )
    if frame["dept_code"].nunique() != 22:
        raise ValueError("El cruce municipal debe cubrir 22 departamentos.")
    return frame.sort_values("code").reset_index(drop=True)


def _find_row(frame: pd.DataFrame, predicate) -> int:
    for index, row in frame.iterrows():
        if predicate(row):
            return int(index)  # type: ignore[arg-type]
    raise ValueError("No se encontró la fila de encabezado esperada.")


def load_census_a1(path: Path, crosswalk: pd.DataFrame) -> dict[str, int]:
    """Municipality population from Census 2018 Table A1.2.

    This value is shown as a reference only; it is never a rate denominator.
    """

    raw = pd.read_excel(path, sheet_name="A1_2", header=None)
    header = _find_row(
        raw,
        lambda row: (
            str(row.iloc[0]).strip() == "Código"
            and str(row.iloc[2]).strip() == "Código"
        ),
    )
    data = raw.iloc[header + 1 :].copy()
    data = data[pd.to_numeric(data.iloc[:, 2], errors="coerce").notna()]
    data = data[data.iloc[:, 0].notna()]
    result: dict[str, int] = {}
    for _, row in data.iterrows():
        census_code = str(int(row.iloc[2])).zfill(4)
        canonical = crosswalk_census_to_projection(census_code)
        population = pd.to_numeric(row.iloc[4], errors="coerce")
        if pd.notna(population):
            result[canonical] = int(population)
    if set(result) != set(crosswalk["code"]):
        missing = sorted(set(crosswalk["code"]) - set(result))
        extra = sorted(set(result) - set(crosswalk["code"]))
        raise ValueError(
            f"Censo A1 no coincide con el cruce. Faltan={missing[:5]} sobran={extra[:5]}"
        )
    if len(result) != 340:
        raise ValueError(f"El censo debe aportar 340 municipios, no {len(result)}.")
    return result


def load_population(path: Path, crosswalk: pd.DataFrame) -> dict[str, int]:
    """2025 total projected population by municipality (both sexes)."""

    frame = pd.read_excel(path)
    year_column = POPULATION_YEAR
    if year_column not in frame.columns:
        raise ValueError(f"La hoja de proyecciones no tiene la columna {year_column}.")
    frame["MUPIO"] = frame["MUPIO"].astype(str).str.zfill(4)
    frame["SEXO"] = frame["SEXO"].astype(str)
    total = frame[frame["SEXO"] == "0"]
    grouped = (
        total.groupby("MUPIO", as_index=False)[year_column]
        .sum()
        .assign(value=lambda d: pd.to_numeric(d[year_column], errors="coerce"))
    )
    result = {str(row.MUPIO): int(row.value) for row in grouped.itertuples()}
    if set(result) != set(crosswalk["code"]):
        missing = sorted(set(crosswalk["code"]) - set(result))
        extra = sorted(set(result) - set(crosswalk["code"]))
        raise ValueError(
            f"Proyecciones no coinciden con el cruce. Faltan={missing[:5]} sobran={extra[:5]}"
        )
    if len(result) != 340:
        raise ValueError(
            f"Las proyecciones deben aportar 340 municipios, no {len(result)}."
        )
    return result


def load_centroids(
    path: Path, crosswalk: pd.DataFrame
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Read the 20,036 populated places and apply the map-layer filters."""

    raw = pd.read_excel(path, header=None)
    header = _find_row(
        raw,
        lambda row: str(row.iloc[6]).strip() == "Longitud",
    )
    data = raw.iloc[header + 1 :].copy()
    data = data[data.iloc[:, 0].notna()]
    data = data[~data.iloc[:, 0].astype(str).str.startswith("Fuente")]
    data = data.iloc[:, :8]
    data.columns = [
        "dept_code",
        "dept_name",
        "muni_code",
        "muni_name",
        "place_code",
        "place_name",
        "lon",
        "lat",
    ]
    data = data.copy()
    data["dept_code"] = data["dept_code"].map(valid_department)
    data["muni_code"] = data["muni_code"].map(canonical_municipality)
    data["place_code"] = data["place_code"].astype(str).str.strip()
    data["place_name"] = data["place_name"].astype(str).str.strip()
    data["lon"] = pd.to_numeric(data["lon"], errors="coerce")
    data["lat"] = pd.to_numeric(data["lat"], errors="coerce")

    source_count = len(data)
    suffix_999 = data["place_code"].str.endswith("999")
    missing_coords = data["lon"].isna() | data["lat"].isna()
    unknown_territory = data["muni_code"].isna() | ~data["muni_code"].isin(
        set(crosswalk["code"])
    )

    keep = ~suffix_999 & ~missing_coords & ~unknown_territory
    cleaned = data.loc[
        keep, ["place_code", "place_name", "muni_code", "dept_code", "lon", "lat"]
    ].copy()
    cleaned["lon"] = cleaned["lon"].round(5)
    cleaned["lat"] = cleaned["lat"].round(5)

    stats = {
        "source_places": int(source_count),
        "excluded_suffix_999": int(suffix_999.sum()),
        "excluded_missing_coordinates": int(missing_coords.sum()),
        "excluded_unknown_territory": int(unknown_territory.sum()),
        "excluded_total": int((~keep).sum()),
        "included": int(keep.sum()),
        "note": (
            "Se excluyen los lugares poblados cuyo código termina en 999 y los que no "
            "tienen longitud/latitud. La capa de puntos es geografía de asentamientos, "
            "no eventos individuales."
        ),
    }
    if stats["included"] + stats["excluded_total"] != stats["source_places"]:
        raise AssertionError("El conteo de la capa de puntos no cuadra.")
    return cleaned.reset_index(drop=True), stats


def load_geojson(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _round_coordinates(value: Any, digits: int = 5) -> Any:
    if isinstance(value, (int, float)):
        return round(float(value), digits)
    if isinstance(value, list):
        return [_round_coordinates(item, digits) for item in value]
    return value


def build_municipal_geojson(path: Path, crosswalk: pd.DataFrame) -> dict[str, Any]:
    source = load_geojson(path)
    shape_to_row = {row.geo_shape_id: row for row in crosswalk.itertuples()}
    features: list[dict[str, Any]] = []
    for feature in source.get("features", []):
        shape_id = feature.get("properties", {}).get("shapeID")
        row = shape_to_row.get(shape_id)
        if row is None:
            continue
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "code": row.code,
                    "name": row.name,
                    "dept": row.dept_code,
                    "deptName": row.dept_name,
                },
                "geometry": {
                    "type": feature["geometry"]["type"],
                    "coordinates": _round_coordinates(
                        feature["geometry"]["coordinates"]
                    ),
                },
            }
        )
    if len(features) != 340:
        raise ValueError(
            f"El GeoJSON municipal debe tener 340 polígonos, no {len(features)}."
        )
    return {"type": "FeatureCollection", "features": features}


def build_department_geojson(path: Path, crosswalk: pd.DataFrame) -> dict[str, Any]:
    source = load_geojson(path)
    code_by_name = {str(name).strip(): code for code, name in DEPARTMENT_NAMES.items()}
    features: list[dict[str, Any]] = []
    for feature in source.get("features", []):
        name = str(feature.get("properties", {}).get("shapeName", "")).strip()
        code = code_by_name.get(name)
        if code is None:
            continue
        features.append(
            {
                "type": "Feature",
                "properties": {"code": code, "name": name},
                "geometry": {
                    "type": feature["geometry"]["type"],
                    "coordinates": _round_coordinates(
                        feature["geometry"]["coordinates"]
                    ),
                },
            }
        )
    if len(features) != 22:
        raise ValueError(
            f"El GeoJSON departamental debe tener 22 polígonos, no {len(features)}."
        )
    return {"type": "FeatureCollection", "features": features}
