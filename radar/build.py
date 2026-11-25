"""Build the JSON bundles consumed by the Next.js application."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from .config import (
    CRITERIA,
    DATA_YEAR,
    DEPARTMENT_NAMES,
    HOMICIDE_SUICIDE_THRESHOLD,
    METRIC_LABELS,
    POPULATION_YEAR,
    PROCESSED_DIR,
    RATE_BASE,
    SUPPRESSION_THRESHOLD,
    TOPICS,
    WEB_DATA_DIR,
)
from .fetch import utc_now
from .normalize import canonical_municipality, department_of
from .reference import (
    build_department_geojson,
    build_municipal_geojson,
    load_census_a1,
    load_centroids,
    load_crosswalk,
    load_population,
)
from .suppress import make_cell, make_count_cell

AGE_BANDS = [f"{start}–{start + 4}" for start in range(0, 80, 5)] + ["80+", "Ignorada"]

CRITERION_NOTES = {
    "residence": (
        "El evento se asigna al municipio de residencia de la persona. El denominador "
        "es la población residente proyectada del territorio."
    ),
    "occurrence": (
        "El evento se asigna al municipio donde ocurrió. La tasa usa la población "
        "residente del territorio como denominador de referencia; no representa la "
        "población expuesta en el lugar del evento."
    ),
}

ROAD_SAFETY_RESIDENCE_REASON = (
    "Las bases de hechos de tránsito, personas fallecidas/lesionadas y vehículos de la "
    "PNC solo identifican el lugar de ocurrencia. No contienen una variable de residencia, "
    "por lo que no se puede calcular este indicador por residencia sin inventar datos."
)


def _json_dump(path: Path, payload: Any, *, pretty: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if pretty:
        text = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text + "\n", encoding="utf-8")
    tmp.replace(path)


def _read(path: Path, usecols: list[str]) -> pd.DataFrame:
    return pd.read_excel(path, usecols=usecols, dtype=str)


def _code_counts(series: pd.Series, known: set[str]) -> tuple[Counter, Counter]:
    """Map raw municipality codes to canonical codes and keep diagnostics."""

    canonical = series.map(canonical_municipality)
    known_mask = canonical.isin(known)
    counts = Counter(canonical[known_mask].astype(str))
    unknown = Counter(series[~known_mask].fillna("(vacío)").astype(str))
    return counts, unknown


def _department_counts(municipal_counts: Counter) -> Counter:
    result: Counter = Counter()
    for code, value in municipal_counts.items():
        result[department_of(code)] += value
    return result


def _level_cells(
    counts: Counter,
    codes: Iterable[str],
    population: dict[str, int],
    threshold: int,
) -> dict[str, Any]:
    cells: dict[str, Any] = {}
    suppressed = 0
    total = 0
    for code in codes:
        count = int(counts.get(code, 0))
        total += count
        cell = make_cell(count, population[code], threshold)
        if cell["suppressed"]:
            suppressed += 1
        cells[code] = cell
    return {
        "cells": cells,
        "suppressed_territories": suppressed,
        "published_territories": len(cells) - suppressed,
        "total_count": total,
    }


def _criterion_payload(
    counts: Counter,
    population: dict[str, int],
    municipal_codes: list[str],
    department_codes: list[str],
    department_population: dict[str, int],
    threshold: int,
    note: str,
) -> dict[str, Any]:
    department_counts = _department_counts(counts)
    national_population = sum(population.values())
    national_count = sum(int(counts.get(code, 0)) for code in municipal_codes)
    national_cell = make_cell(national_count, national_population, threshold)
    return {
        "available": True,
        "note": note,
        "threshold": threshold,
        "national": national_cell,
        "levels": {
            "department": _level_cells(
                department_counts, department_codes, department_population, threshold
            ),
            "municipality": _level_cells(
                counts, municipal_codes, population, threshold
            ),
        },
    }


def _unavailable(reason: str) -> dict[str, Any]:
    return {"available": False, "reason": reason}


def _metric_meta(metric: str, unit: str, description: str) -> dict[str, Any]:
    return {
        "id": metric,
        "label": METRIC_LABELS[metric],
        "unit": unit,
        "description": description,
    }


def _cause_group(value: Any) -> str:
    code = str(value or "").strip().upper()
    if not code:
        return "other"
    if code.startswith("V"):
        return "traffic"
    if re.match(r"^X(6\d|7\d|8[0-4])", code):
        return "suicide"
    if re.match(r"^(X(8[5-9]|9\d)|Y0\d)", code):
        return "homicide"
    return "other"


def _age_index(value: Any) -> int:
    try:
        age = int(float(str(value).strip()))
    except (TypeError, ValueError):
        return 17
    # INE uses 999 (and sometimes 9999) as the unknown-age sentinel; it must
    # not be lumped into the 80+ band.
    if age < 0 or age in {999, 9999} or age > 120:
        return 17
    if age >= 80:
        return 16
    return age // 5


def _age_cells(series: pd.Series) -> list[dict[str, Any]]:
    counts = Counter(_age_index(value) for value in series)
    return [
        make_count_cell(int(counts.get(index, 0)), SUPPRESSION_THRESHOLD)
        for index in range(18)
    ]


def _age_profile_for_criterion(
    frame: pd.DataFrame,
    age_column: str,
    municipality_column: str,
    codes: list[str],
) -> dict[str, Any]:
    frame = frame.copy()
    frame["_muni"] = frame[municipality_column].map(canonical_municipality)
    frame = frame[frame["_muni"].isin(codes)]
    national = _age_cells(frame[age_column])
    departments: dict[str, list[dict[str, Any]]] = {}
    for dept, group in frame.groupby(frame["_muni"].str[:2]):
        departments[str(dept)] = _age_cells(group[age_column])
    return {"national": national, "departments": departments}


def build(
    raw_dir: Path,
    reference_dir: Path,
    web_dir: Path,
    provenance: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute every output and write it into ``web/public/data``."""

    crosswalk = load_crosswalk(reference_dir / "municipios_crosswalk.csv")
    municipal_codes = crosswalk["code"].tolist()
    department_codes = sorted(DEPARTMENT_NAMES)
    code_to_dept = dict(zip(crosswalk["code"], crosswalk["dept_code"]))
    population = load_population(
        raw_dir / "proyecciones_poblacion_2015_2030.xlsx", crosswalk
    )
    census = load_census_a1(raw_dir / "censo_2018_cuadro_a1.xlsx", crosswalk)
    places, point_stats = load_centroids(
        raw_dir / "centroides_lugares_poblados_2018.xlsx", crosswalk
    )
    department_population: dict[str, int] = {
        code: sum(population[m] for m in municipal_codes if code_to_dept[m] == code)
        for code in department_codes
    }

    known = set(municipal_codes)
    diagnostics: dict[str, Any] = {}

    # ------------------------------------------------------------------ births
    births = _read(
        raw_dir / "nacimientos_2025.xlsx",
        ["Depreg", "Mupreg", "Depocu", "Mupocu", "Añoocu", "Edadp"],
    )
    births = births[births["Añoocu"].astype(str).str.strip() == str(DATA_YEAR)]
    births_res, births_res_unknown = _code_counts(births["Mupreg"], known)
    births_occ, births_occ_unknown = _code_counts(births["Mupocu"], known)
    diagnostics["births"] = {
        "records": int(len(births)),
        "residence_unmapped": int(sum(births_res_unknown.values())),
        "occurrence_unmapped": int(sum(births_occ_unknown.values())),
        "unmapped_codes": {
            "residence": dict(births_res_unknown.most_common(10)),
            "occurrence": dict(births_occ_unknown.most_common(10)),
        },
    }

    # ------------------------------------------------------------------ deaths
    deaths = _read(
        raw_dir / "defunciones_2025.xlsx",
        ["Depreg", "Mupreg", "Depocu", "Mupocu", "Añoocu", "Edadif", "Caudef"],
    )
    deaths = deaths[deaths["Añoocu"].astype(str).str.strip() == str(DATA_YEAR)]
    deaths["_cause"] = deaths["Caudef"].map(_cause_group)
    deaths_res, deaths_res_unknown = _code_counts(deaths["Mupreg"], known)
    deaths_occ, deaths_occ_unknown = _code_counts(deaths["Mupocu"], known)
    deaths_res_causes = {
        cause: _code_counts(deaths.loc[deaths["_cause"] == cause, "Mupreg"], known)[0]
        for cause in ("other", "homicide", "suicide", "traffic")
    }
    deaths_occ_causes = {
        cause: _code_counts(deaths.loc[deaths["_cause"] == cause, "Mupocu"], known)[0]
        for cause in ("other", "homicide", "suicide", "traffic")
    }
    diagnostics["deaths"] = {
        "records": int(len(deaths)),
        "residence_unmapped": int(sum(deaths_res_unknown.values())),
        "occurrence_unmapped": int(sum(deaths_occ_unknown.values())),
        "unmapped_codes": {
            "residence": dict(deaths_res_unknown.most_common(10)),
            "occurrence": dict(deaths_occ_unknown.most_common(10)),
        },
        "causes": {
            "homicide": int((deaths["_cause"] == "homicide").sum()),
            "suicide": int((deaths["_cause"] == "suicide").sum()),
            "traffic": int((deaths["_cause"] == "traffic").sum()),
            "other": int((deaths["_cause"] == "other").sum()),
        },
    }

    # ------------------------------------------------------------- road safety
    incidents = _read(
        raw_dir / "base-de-datos-hechos-de-transito-pnc-2025.xlsx",
        ["año_ocu", "mupio_ocu"],
    )
    incidents = incidents[
        incidents["año_ocu"].astype(str).str.strip() == str(DATA_YEAR)
    ]
    incident_counts, incident_unknown = _code_counts(incidents["mupio_ocu"], known)

    victims = _read(
        raw_dir / "base-de-datos-fallecidos-y-lesionados-pnc-2025.xlsx",
        ["año_ocu", "mupio_ocu", "fall_les", "edad_quinquenales"],
    )
    victims = victims[victims["año_ocu"].astype(str).str.strip() == str(DATA_YEAR)]
    fatalities = victims[victims["fall_les"].astype(str).str.strip() == "1"]
    injuries = victims[victims["fall_les"].astype(str).str.strip() == "2"]
    ignored_victims = victims[
        ~victims.index.isin(fatalities.index) & ~victims.index.isin(injuries.index)
    ]
    fatality_counts, fatality_unknown = _code_counts(fatalities["mupio_ocu"], known)
    injury_counts, injury_unknown = _code_counts(injuries["mupio_ocu"], known)

    vehicles = _read(
        raw_dir / "base-de-datos-vehiculos-involucrados-pnc-2025.xlsx",
        ["año_ocu", "mupio_ocu"],
    )
    vehicles = vehicles[vehicles["año_ocu"].astype(str).str.strip() == str(DATA_YEAR)]
    vehicle_counts, vehicle_unknown = _code_counts(vehicles["mupio_ocu"], known)

    diagnostics["road_safety"] = {
        "incidents": {
            "records": int(len(incidents)),
            "unmapped": int(sum(incident_unknown.values())),
            "unmapped_codes": dict(incident_unknown.most_common(10)),
        },
        "fatalities": {
            "records": int(len(fatalities)),
            "unmapped": int(sum(fatality_unknown.values())),
            "unmapped_codes": dict(fatality_unknown.most_common(10)),
        },
        "injuries": {
            "records": int(len(injuries)),
            "unmapped": int(sum(injury_unknown.values())),
            "unmapped_codes": dict(injury_unknown.most_common(10)),
        },
        "vehicles": {
            "records": int(len(vehicles)),
            "unmapped": int(sum(vehicle_unknown.values())),
            "unmapped_codes": dict(vehicle_unknown.most_common(10)),
        },
        "victims_ignored_status": int(len(ignored_victims)),
    }

    # ------------------------------------------------------------- indicators
    topics: dict[str, Any] = {}

    road_metrics = {
        "incidents": _metric_meta(
            "incidents",
            "hechos",
            "Un registro por hecho de tránsito reportado por la PNC.",
        ),
        "fatalities": _metric_meta(
            "fatalities",
            "personas",
            "Personas fallecidas en hechos de tránsito (fall_les = 1).",
        ),
        "injuries": _metric_meta(
            "injuries",
            "personas",
            "Personas lesionadas en hechos de tránsito (fall_les = 2).",
        ),
        "vehicles": _metric_meta(
            "vehicles",
            "vehículos",
            "Vehículos involucrados. No se publican marca, color ni modelo.",
        ),
    }
    for key, count_map in (
        ("incidents", incident_counts),
        ("fatalities", fatality_counts),
        ("injuries", injury_counts),
        ("vehicles", vehicle_counts),
    ):
        occurrence = _criterion_payload(
            count_map,
            population,
            municipal_codes,
            department_codes,
            department_population,
            SUPPRESSION_THRESHOLD,
            CRITERION_NOTES["occurrence"],
        )
        road_metrics[key]["criteria"] = {
            "residence": _unavailable(ROAD_SAFETY_RESIDENCE_REASON),
            "occurrence": occurrence,
        }
    topics["road_safety"] = {
        **TOPICS["road_safety"],
        "metrics": road_metrics,
        "onlyOccurrence": True,
    }

    birth_metric = _metric_meta(
        "births", "nacimientos", "Nacimientos registrados en el año 2025."
    )
    birth_metric["criteria"] = {
        "residence": _criterion_payload(
            births_res,
            population,
            municipal_codes,
            department_codes,
            department_population,
            SUPPRESSION_THRESHOLD,
            CRITERION_NOTES["residence"],
        ),
        "occurrence": _criterion_payload(
            births_occ,
            population,
            municipal_codes,
            department_codes,
            department_population,
            SUPPRESSION_THRESHOLD,
            CRITERION_NOTES["occurrence"],
        ),
    }
    topics["births"] = {**TOPICS["births"], "metrics": {"births": birth_metric}}

    death_metric = _metric_meta(
        "deaths", "defunciones", "Todas las defunciones ocurridas en el año 2025."
    )
    death_metric["criteria"] = {
        "residence": _criterion_payload(
            deaths_res,
            population,
            municipal_codes,
            department_codes,
            department_population,
            SUPPRESSION_THRESHOLD,
            CRITERION_NOTES["residence"],
        ),
        "occurrence": _criterion_payload(
            deaths_occ,
            population,
            municipal_codes,
            department_codes,
            department_population,
            SUPPRESSION_THRESHOLD,
            CRITERION_NOTES["occurrence"],
        ),
    }
    topics["deaths"] = {**TOPICS["deaths"], "metrics": {"deaths": death_metric}}

    # ---------------------------------------------------------- death causes
    cause_specs = (
        ("all", "Todas las causas", SUPPRESSION_THRESHOLD),
        ("homicide", METRIC_LABELS["homicide"], HOMICIDE_SUICIDE_THRESHOLD),
        ("suicide", METRIC_LABELS["suicide"], HOMICIDE_SUICIDE_THRESHOLD),
        ("traffic", METRIC_LABELS["traffic"], SUPPRESSION_THRESHOLD),
    )
    death_causes: dict[str, Any] = {}
    for criterion, base_counts, cause_counts in (
        ("residence", deaths_res, deaths_res_causes),
        ("occurrence", deaths_occ, deaths_occ_causes),
    ):
        criterion_payload: dict[str, Any] = {
            "criterion": criterion,
            "note": CRITERION_NOTES[criterion],
            "causes": {
                key: {"label": label, "threshold": threshold}
                for key, label, threshold in cause_specs
            },
            "national": {},
            "levels": {"department": {}, "municipality": {}},
        }
        for key, _label, threshold in cause_specs:
            counts = base_counts if key == "all" else cause_counts[key]
            criterion_payload["national"][key] = make_cell(
                sum(int(counts.get(code, 0)) for code in municipal_codes),
                sum(population.values()),
                threshold,
            )
            for level, codes, pops in (
                ("department", department_codes, department_population),
                ("municipality", municipal_codes, population),
            ):
                if level == "department":
                    level_counts = _department_counts(counts)
                else:
                    level_counts = counts
                criterion_payload["levels"][level].setdefault("cells", {})
                for code in codes:
                    cell = make_cell(
                        int(level_counts.get(code, 0)), pops[code], threshold
                    )
                    criterion_payload["levels"][level]["cells"].setdefault(code, {})[
                        key
                    ] = cell
        for level, codes in (
            ("department", department_codes),
            ("municipality", municipal_codes),
        ):
            criterion_payload["levels"][level]["suppressed_territories"] = {
                key: sum(
                    1
                    for code in codes
                    if criterion_payload["levels"][level]["cells"][code][key][
                        "suppressed"
                    ]
                )
                for key, _label, _threshold in cause_specs
            }
        death_causes[criterion] = criterion_payload

    # ------------------------------------------------------------- age bands
    age_profile: dict[str, Any] = {
        "bands": AGE_BANDS,
        "note": (
            "Edades agrupadas en bandas quinquenales. Ninguna celda muestra edades "
            "individuales. El perfil se publica a nivel nacional y departamental para "
            "evitar cruces municipio × edad con conteos pequeños."
        ),
        "topics": {},
    }
    age_profile["topics"]["births"] = {
        "label": "Edad de la madre",
        "criteria": {
            "residence": _age_profile_for_criterion(
                births,
                "Edadp",
                "Mupreg",
                municipal_codes,
            ),
            "occurrence": _age_profile_for_criterion(
                births,
                "Edadp",
                "Mupocu",
                municipal_codes,
            ),
        },
    }
    age_profile["topics"]["deaths"] = {
        "label": "Edad al fallecer",
        "criteria": {
            "residence": _age_profile_for_criterion(
                deaths,
                "Edadif",
                "Mupreg",
                municipal_codes,
            ),
            "occurrence": _age_profile_for_criterion(
                deaths,
                "Edadif",
                "Mupocu",
                municipal_codes,
            ),
        },
    }

    # ------------------------------------------------------------ territories
    department_rows = []
    for code in department_codes:
        members = [m for m in municipal_codes if code_to_dept[m] == code]
        department_rows.append(
            {
                "code": code,
                "name": DEPARTMENT_NAMES[code],
                "population": department_population[code],
                "census2018": sum(census[m] for m in members),
                "municipalities": len(members),
            }
        )

    place_centroids = places.groupby("muni_code")[["lon", "lat"]].median().reset_index()
    centroid_by_code = {
        row.muni_code: (round(float(row.lon), 5), round(float(row.lat), 5))
        for row in place_centroids.itertuples()
    }
    municipality_rows = []
    for row in crosswalk.itertuples():
        lon, lat = centroid_by_code.get(row.code, (None, None))
        municipality_rows.append(
            {
                "code": row.code,
                "name": row.name,
                "dept": row.dept_code,
                "deptName": row.dept_name,
                "population": population[row.code],
                "census2018": census[row.code],
                "lon": lon,
                "lat": lat,
            }
        )

    territories = {
        "departments": department_rows,
        "municipalities": municipality_rows,
    }

    # --------------------------------------------------------------- outputs
    point_payload = {
        "fields": ["id", "name", "muni", "dept", "lon", "lat"],
        "points": [
            [
                str(row.place_code),
                str(row.place_name),
                str(row.muni_code),
                str(row.dept_code),
                float(row.lon),
                float(row.lat),
            ]
            for row in places.itertuples()
        ],
        "filters": point_stats,
    }

    generated_at = utc_now()
    meta = {
        "schemaVersion": 1,
        "title": "Radar territorial de seguridad vial y salud",
        "subtitle": "Guatemala · nacimientos, defunciones y siniestralidad vial 2025",
        "generatedAtUtc": generated_at,
        "dataYear": DATA_YEAR,
        "populationYear": POPULATION_YEAR,
        "rateBase": RATE_BASE,
        "topics": {
            key: {"label": value["label"], "description": value["description"]}
            for key, value in TOPICS.items()
        },
        "criteria": CRITERIA,
        "criterionNotes": CRITERION_NOTES,
        "thresholds": {
            "general": SUPPRESSION_THRESHOLD,
            "homicideSuicide": HOMICIDE_SUICIDE_THRESHOLD,
            "rateBase": RATE_BASE,
        },
        "suppression": {
            "law": "Decreto-Ley 3-85 (Ley Orgánica del INE) y su reglamento",
            "general": SUPPRESSION_THRESHOLD,
            "homicideSuicide": HOMICIDE_SUICIDE_THRESHOLD,
            "text": (
                "Toda celda con menos de 5 casos se suprime. Los homicidios y suicidios "
                "desagregados se suprimen con menos de 10 casos. Una celda suprimida no "
                "publica conteo ni tasa: el secreto estadístico protege a las personas."
            ),
            "smallCellPolicy": (
                "No se publican cruces municipio × día. Los desgloses de causa y los "
                "perfiles de edad aplican los mismos umbrales; el perfil de edad se limita "
                "a nivel departamental. Los vehículos se muestran solo como conteo, sin "
                "marca, color ni modelo."
            ),
        },
        "population": {
            "year": POPULATION_YEAR,
            "source": (
                "INE, Estimaciones y proyecciones de la población total por municipio "
                "según sexo y edad, 2015–2030."
            ),
            "note": (
                "El denominador de todas las tasas es la población total proyectada 2025 "
                "(ambos sexos). El Censo 2018 se muestra únicamente como referencia y "
                "nunca se usa para calcular tasas."
            ),
            "projectionHorizon": "2015–2030",
            "projectionNote": (
                "La serie oficial disponible en el banco de datos del INE llega a 2030; "
                "no se extrapola a 2035. El año de análisis es 2025."
            ),
        },
        "pointLayer": point_stats,
        "coverage": {
            "municipalities": len(municipal_codes),
            "departments": len(department_codes),
            "crosswalk": (
                "Los 16 municipios del departamento de Guatemala usan el cruce +21 entre "
                "el Censo 2018 (0102–0117) y las proyecciones (0123–0138)."
            ),
            "diagnostics": diagnostics,
        },
        "provenance": provenance,
        "limits": [
            "Los registros de tránsito de la PNC solo tienen lugar de ocurrencia; no permiten un análisis por residencia.",
            "Una tasa por ocurrencia usa población residente como denominador de referencia y no mide exposición en el lugar del evento.",
            "Las proyecciones municipales oficiales disponibles llegan a 2030; el análisis se concentra en 2025.",
            "El registro 0930 de defunciones no corresponde a un municipio del cruce de 340 y se excluye de los totales territoriales (se informa como no mapeado).",
            "La capa de puntos representa lugares poblados del Censo 2018, no la ubicación de cada evento.",
            "Los códigos 999 de edad se tratan como ignorados; no se imputan y se informan aparte del perfil de edad.",
            "Las asociaciones territoriales son descriptivas y no implican causalidad.",
        ],
        "licenses": [
            {
                "name": "Datos INE",
                "detail": "Datos abiertos del Instituto Nacional de Estadística de Guatemala; se cita la fuente en la aplicación y en este README.",
            },
            {
                "name": "geoBoundaries / OCHA FISS",
                "detail": "CC BY 3.0 IGO. Límites administrativos municipales y departamentales.",
                "url": "https://www.geoboundaries.org/",
            },
            {
                "name": "Código de la aplicación",
                "detail": "MIT.",
            },
        ],
        "aiDisclosure": (
            "Este proyecto fue desarrollado con asistencia de herramientas de inteligencia "
            "artificial generativa (OpenCode y modelos de lenguaje) para redacción de código, "
            "revisión y documentación. El equipo revisa y defiende el código y las decisiones "
            "metodológicas; la IA no sustituye la validación de los datos oficiales."
        ),
        "methodology": {
            "residenceVsOccurrence": (
                "Residencia y ocurrencia son criterios distintos y nunca se suman entre sí. "
                "Cada vista declara el criterio activo y su nota metodológica."
            ),
            "rates": (
                "Tasa = casos / población proyectada 2025 × 10,000. No se mezclan conteos "
                "censales con población proyectada."
            ),
            "suppression": (
                "Los conteos y tasas por debajo del umbral se sustituyen por una marca de "
                "supresión; no se publica ningún valor numérico de la celda."
            ),
        },
    }

    output_dir = web_dir
    _json_dump(output_dir / "meta.json", meta, pretty=True)
    _json_dump(output_dir / "territories.json", territories)
    _json_dump(
        output_dir / "indicators.json",
        {
            "generatedAtUtc": generated_at,
            "dataYear": DATA_YEAR,
            "rateBase": RATE_BASE,
            "topics": topics,
        },
    )
    _json_dump(output_dir / "death-causes.json", death_causes)
    _json_dump(output_dir / "age-profile.json", age_profile)
    _json_dump(output_dir / "points.json", point_payload)
    _json_dump(
        output_dir / "municipios.geojson",
        build_municipal_geojson(reference_dir / "gtm_adm2.geojson", crosswalk),
    )
    _json_dump(
        output_dir / "departamentos.geojson",
        build_department_geojson(reference_dir / "gtm_adm1.geojson", crosswalk),
    )

    # A copy for offline analysts who prefer the processed folder.
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    for name in (
        "meta.json",
        "indicators.json",
        "territories.json",
        "death-causes.json",
        "age-profile.json",
    ):
        target = PROCESSED_DIR / name
        target.write_bytes((output_dir / name).read_bytes())

    return {
        "generatedAtUtc": generated_at,
        "municipalities": len(municipal_codes),
        "points": point_stats["included"],
        "outputDir": str(output_dir),
    }
