"""End-to-end build: cache -> normalise -> join -> indicators -> outputs.

Run with::

    uv run build-pressure

The command is safe to re-run. Existing raw files are reused; missing files are
downloaded from the closed URL registry. Outputs are written to
``data/processed`` and mirrored to ``web/public/data`` for the static frontend.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .download import (
    ensure_all,
    file_for,
    load_manifest,
    sha256_file,
    utc_now,
    iso_utc,
)
from .education import load_establishments, load_students
from .indicators import (
    INDICATOR_DEFINITIONS,
    PRESSURE_CLASS_LABELS,
    PRESSURE_INDICATOR_KEYS,
    build_indicators,
)
from .normalize import assert_unique_codes
from .projections import (
    build_reference_catalog,
    load_projection_2030,
    load_projection_2035,
    validate_overlap,
)
from .segeplan import load_allocation, load_poverty
from .sources import SOURCE_BY_ID, SOURCES, VERIFIED_ON
from .suppression import suppression_metadata
from .vital import load_births, load_deaths


SNAPSHOT_ID = "2026-11-24"
BASE_COLUMNS = [
    "municipio_codigo",
    "municipio_nombre",
    "departamento_codigo",
    "departamento_nombre",
    "poblacion_2015",
    "poblacion_2025",
    "poblacion_2030",
    "poblacion_2030_ckan",
    "poblacion_2035",
    "crecimiento_abs_2025_2035",
    "crecimiento_poblacional_pct",
    "crecimiento_poblacional_pct_2015_2025",
    "nacimientos_2025",
    "defunciones_2025",
    "defunciones_menores_5_2025",
    "nacimientos_por_1000_habitantes_2025",
    "tasa_mortalidad_general_2025",
    "tasa_mortalidad_menor_5_2025",
    "relacion_nacimientos_defunciones_2025",
    "escuelas_2022",
    "escuelas_publicas_2022",
    "estudiantes_2022",
    "estudiantes_publicos_2022",
    "nacimientos_por_escuela_2025",
    "estudiantes_por_escuela_2022",
    "nacimientos_por_100_estudiantes_2025",
    "escuelas_por_10000_habitantes_2022",
    "estudiantes_por_10000_habitantes_2022",
    "pobreza_general_pct_2023",
    "pobreza_extrema_pct_2023",
    "poblacion_en_pobreza_2023",
    "poblacion_en_pobreza_extrema_2023",
    "brecha_pobreza_general_2023",
    "severidad_pobreza_general_2023",
    "consumo_promedio_q_mes_2023",
    "asignacion_constitucional_2026_gtq",
    "poblacion_asignacion_2025",
    "asignacion_por_habitante_2026_gtq",
    "asignacion_presion_indice_2026",
    "ingresos_propios_2024_gtq",
    "ingresos_propios_per_capita_2024_gtq",
    "aldeas_caserios_2025",
]


LIMITATIONS = [
    "Las proyecciones municipales son escenarios, no predicciones. La serie 2015-2035 corresponde a la actualización 2020 y puede perder vigencia lejos del período de estimación.",
    "La serie larga 2015-2030 numera los 16 municipios del departamento de Guatemala como 0123-0138. La aplicación aplica el cruce +21 para llevarlos a 0102-0117 y valida el traslape 2015-2030 contra la serie 2015-2035.",
    "MINEDUC publica establecimientos y matrícula hasta 2022. La razón nacimientos 2025 / escuelas 2022 compara un numerador de 2025 con una oferta de 2022; es una aproximación de carga, no una medición de alumnos por aula.",
    "La incidencia de pobreza extrema 2023 no está publicada para 23 municipios. Se muestra como no disponible, no como cero.",
    "La asignación constitucional 2026 es un cálculo matemático, no la ejecución presupuestaria. La población de referencia es la utilizada por SEGEPLAN en el cálculo.",
    "Las clases de presión son percentiles relativos dentro de los 340 municipios. No son umbrales oficiales del INE ni una calificación de desempeño municipal.",
    "Los conteos no nulos menores que 5 se suprimen, junto con las tasas derivadas que los usan. Es una salvaguarda conservadora de secreto estadístico, no una marca oficial de supresión del INE.",
    "La herramienta es analítica y descriptiva. No identifica personas, hogares ni empresas y no establece relaciones causales.",
    "No es un sistema oficial del INE ni un producto interinstitucional. Las fuentes conservan sus licencias y atribuciones.",
    "Los datos de SEGEPLAN están bajo CC BY-NC 2.0: uso no comercial únicamente. Cualquier reutilización comercial requiere autorización.",
]


DISCLAIMER = (
    "Herramienta analítica independiente. No es un sistema oficial del INE ni un "
    "producto interinstitucional. Las comparaciones son descriptivas y no implican "
    "causalidad. Verifique siempre la fuente y la fecha de descarga."
)

AI_DISCLOSURE = (
    "Este prototipo fue desarrollado con asistencia de inteligencia artificial "
    "(DeepSeek V4.1 Flash a través de OpenCode). El equipo revisa, comprende y "
    "asume la responsabilidad del código, de la interpretación de los datos y de "
    "las conclusiones. La declaración completa está en el README."
)


def _native(value: Any) -> Any:
    """Convert pandas/numpy scalars to JSON-safe Python values."""

    if value is None or value is pd.NA:
        return None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        number = float(value)
        return None if math.isnan(number) or math.isinf(number) else number
    if isinstance(value, float):
        return None if math.isnan(value) or math.isinf(value) else value
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if isinstance(value, (np.ndarray, list, tuple)):
        return [_native(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _native(item) for key, item in value.items()}
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def _records(frame: pd.DataFrame) -> list[dict]:
    suppressed_fields = [
        column for column in frame.columns if column.endswith("_suprimido")
    ]
    pressure_fields = [
        column
        for column in frame.columns
        if column.endswith("_percentil")
        or column.endswith("_rank_nacional")
        or column.endswith("_rank_departamento")
        or column.endswith("_clase")
    ]
    value_columns = [column for column in BASE_COLUMNS if column in frame.columns]
    records: list[dict] = []
    for _, row in frame.iterrows():
        record = {column: _native(row[column]) for column in value_columns}
        record["campos_suprimidos"] = [
            field.removesuffix("_suprimido")
            for field in suppressed_fields
            if bool(row.get(field, False))
        ]
        record["tiene_supresion"] = bool(record["campos_suprimidos"])
        pressure: dict[str, dict] = {}
        for definition in INDICATOR_DEFINITIONS:
            key = definition["key"]
            if not definition.get("rank"):
                continue
            if f"{key}_clase" not in frame.columns:
                continue
            pressure[key] = {
                "percentil": _native(row.get(f"{key}_percentil")),
                "rank_nacional": _native(row.get(f"{key}_rank_nacional")),
                "rank_departamento": _native(row.get(f"{key}_rank_departamento")),
                "clase": _native(row.get(f"{key}_clase")),
            }
        record["presion"] = pressure
        records.append(record)
    return records


def _departments(frame: pd.DataFrame) -> list[dict]:
    grouped = frame.groupby(
        ["departamento_codigo", "departamento_nombre"], as_index=False
    ).agg(
        municipios=("municipio_codigo", "nunique"),
        poblacion_2025=("poblacion_2025", "sum"),
        nacimientos_2025=("nacimientos_2025", "sum"),
        escuelas_2022=("escuelas_2022", "sum"),
        estudiantes_2022=("estudiantes_2022", "sum"),
        asignacion_constitucional_2026_gtq=(
            "asignacion_constitucional_2026_gtq",
            "sum",
        ),
        pobreza_general_pct_2023=("pobreza_general_pct_2023", "mean"),
    )
    departments = []
    for _, row in grouped.sort_values("departamento_codigo").iterrows():
        departments.append(
            {
                "codigo": _native(row["departamento_codigo"]),
                "nombre": _native(row["departamento_nombre"]),
                "municipios": _native(row["municipios"]),
                "poblacion_2025": _native(row["poblacion_2025"]),
                "nacimientos_2025": _native(row["nacimientos_2025"]),
                "escuelas_2022": _native(row["escuelas_2022"]),
                "estudiantes_2022": _native(row["estudiantes_2022"]),
                "asignacion_constitucional_2026_gtq": _native(
                    row["asignacion_constitucional_2026_gtq"]
                ),
                "pobreza_general_pct_2023": _native(row["pobreza_general_pct_2023"]),
            }
        )
    return departments


def _highlights(frame: pd.DataFrame, limit: int = 5) -> dict:
    highlights: dict[str, list[dict]] = {}
    for key in PRESSURE_INDICATOR_KEYS:
        if key not in frame.columns:
            continue
        subset = frame[frame[key].notna()].nlargest(limit, key)
        highlights[key] = [
            {
                "codigo": _native(row["municipio_codigo"]),
                "municipio": _native(row["municipio_nombre"]),
                "departamento": _native(row["departamento_nombre"]),
                "valor": _native(row[key]),
                "clase": _native(row.get(f"{key}_clase")),
            }
            for _, row in subset.iterrows()
        ]
    return highlights


def _source_records(manifest: dict, data_dir: Path) -> list[dict]:
    records: list[dict] = []
    files = manifest.get("files", {})
    for source in SOURCES:
        record = source.as_dict()
        cached = files.get(source.id, {})
        local_name = cached.get("filename") or source.filename
        local_path = (Path(data_dir) / local_name).as_posix()
        record.update(
            {
                "downloaded_at_utc": cached.get("downloaded_at_utc"),
                "download_status": cached.get("download_status"),
                "sha256": cached.get("sha256"),
                "bytes": cached.get("bytes"),
                "http_status": cached.get("http_status"),
                "content_type": cached.get("content_type"),
                "local_path": local_path,
            }
        )
        record["license_status"] = record["license"]["status"]
        record["ckan_license_id"] = record["license"]["ckan_license_id"]
        record["non_commercial"] = record["license"]["commercial_use"] is False
        if record["non_commercial"]:
            record["license_notice"] = (
                "CC BY-NC 2.0: uso no comercial únicamente; se requiere "
                "atribución a SEGEPLAN."
            )
        elif record["license"]["commercial_use"] is True:
            record["license_notice"] = "Reutilización permitida con atribución."
        else:
            record["license_notice"] = (
                "Licencia no declarada; cite la fuente y verifique los términos."
            )
        records.append(record)

    # The 340-municipality catalogue is derived from the official 2015-2035 table.
    base = next(record for record in records if record["id"] == "ine-proyecciones-2035")
    records.append(
        {
            "id": "ine-catalogo-municipal-340",
            "title": "Catálogo de referencia de los 340 municipios",
            "publisher": "Derivado de la tabla municipal oficial del INE",
            "dataset_page": base["dataset_page"],
            "download_url": base["download_url"],
            "filename": "municipios_gt_340.csv",
            "format": "derived-csv",
            "license": base["license"],
            "license_status": base["license"]["status"],
            "ckan_license_id": base["license"]["ckan_license_id"],
            "attribution": base["attribution"],
            "description": (
                "Catálogo construido a partir de las 340 filas municipales de la "
                "proyección 2015-2035. Se validó contra los 340 códigos de "
                "MINEDUC, SEGEPLAN y la proyección larga 2015-2030."
            ),
            "verified_on": VERIFIED_ON,
            "downloaded_at_utc": base.get("downloaded_at_utc"),
            "download_status": "derived",
            "sha256": base.get("sha256"),
            "bytes": None,
            "http_status": None,
            "content_type": "text/csv",
            "local_path": "data/reference/municipios_gt_340.csv",
            "non_commercial": False,
            "license_notice": base.get("license_notice"),
        }
    )
    return records


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def _copy_if_changed(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def build_all(
    data_dir: Path = Path("data"),
    out_dir: Path = Path("data/processed"),
    web_public: Path | None = Path("web/public/data"),
    *,
    fetcher=None,
    skip_download: bool = False,
    verbose: bool = True,
) -> dict:
    data_dir = Path(data_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if skip_download:
        manifest = load_manifest(data_dir)
        for source in SOURCES:
            file_for(source.id, data_dir)
    else:
        manifest = ensure_all(data_dir, fetcher=fetcher)

    paths = {source.id: file_for(source.id, data_dir) for source in SOURCES}

    if verbose:
        print("[1/6] Leyendo proyecciones municipales…")
    projection_2035, meta_2035 = load_projection_2035(paths["ine-proyecciones-2035"])
    projection_2030, meta_2030 = load_projection_2030(paths["ine-proyecciones-2030"])
    overlap = validate_overlap(projection_2035, projection_2030)
    reference = build_reference_catalog(projection_2035)
    reference_codes = set(reference["municipio_codigo"].astype(str))
    assert_unique_codes(reference["municipio_codigo"], "catálogo final")

    if verbose:
        print("[2/6] Agregando nacimientos y defunciones 2025…")
    births, meta_births = load_births(paths["ine-nacimientos-2025"], reference_codes)
    deaths, meta_deaths = load_deaths(paths["ine-defunciones-2025"], reference_codes)

    if verbose:
        print("[3/6] Agregando establecimientos y estudiantes MINEDUC…")
    establishments, meta_establishments = load_establishments(
        paths["mineduc-establecimientos-2022"], reference_codes
    )
    students, meta_students = load_students(
        paths["mineduc-estudiantes-2022"], reference_codes
    )

    if verbose:
        print("[4/6] Leyendo pobreza y asignación constitucional de SEGEPLAN…")
    poverty, meta_poverty = load_poverty(
        paths["segeplan-pobreza-2023"], reference_codes
    )
    allocation, meta_allocation = load_allocation(
        paths["segeplan-asignacion-2026"], reference_codes
    )

    if verbose:
        print("[5/6] Construyendo indicadores y aplicando supresión…")
    frame, indicator_meta = build_indicators(
        reference,
        projection_2035,
        projection_2030,
        births,
        deaths,
        establishments,
        students,
        poverty,
        allocation,
    )

    # Write the reference catalogue as CSV inside data/reference for auditors.
    reference_dir = data_dir / "reference"
    reference_dir.mkdir(parents=True, exist_ok=True)
    reference_path = reference_dir / "municipios_gt_340.csv"
    reference.to_csv(reference_path, index=False, encoding="utf-8")

    if verbose:
        print("[6/6] Escribiendo Parquet, JSON y manifiesto de procedencia…")
    reference.to_parquet(out_dir / "municipios.parquet", index=False)
    frame.to_parquet(out_dir / "indicators.parquet", index=False)

    generated_at = iso_utc(utc_now())
    sources = _source_records(manifest, data_dir)
    municipalities = _records(frame)
    departments_list = _departments(frame)

    indicator_metadata = []
    for definition in INDICATOR_DEFINITIONS:
        indicator_metadata.append(
            {
                **definition,
                "source_metadata": [
                    next(
                        (
                            {
                                "id": source["id"],
                                "title": source["title"],
                                "license": source["license"],
                                "downloaded_at_utc": source["downloaded_at_utc"],
                                "download_url": source["download_url"],
                            }
                        )
                        for source in sources
                        if source["id"] == source_id
                    )
                    for source_id in definition["sources"]
                ],
            }
        )

    payload = {
        "snapshot_id": SNAPSHOT_ID,
        "generated_at_utc": generated_at,
        "verified_on": VERIFIED_ON,
        "title": "Monitor de presión de servicios y crecimiento local",
        "subtitle": (
            "Comparación municipal de crecimiento poblacional, nacimientos, "
            "oferta escolar, pobreza y asignación constitucional en Guatemala."
        ),
        "disclaimer": DISCLAIMER,
        "ai_disclosure": AI_DISCLOSURE,
        "municipality_count": int(len(frame)),
        "department_count": int(frame["departamento_codigo"].nunique()),
        "indicators": indicator_metadata,
        "pressure_indicator_keys": PRESSURE_INDICATOR_KEYS,
        "pressure_class_labels": PRESSURE_CLASS_LABELS,
        "departments": departments_list,
        "municipalities": municipalities,
        "summary": {
            "national_totals": indicator_meta["national_totals"],
            "pressure_classes": indicator_meta["pressure_classes"],
            "national_per_capita_allocation_2026_gtq": indicator_meta[
                "national_per_capita_allocation_2026_gtq"
            ],
            "municipalities_with_complete_pressure": indicator_meta[
                "municipalities_with_complete_pressure"
            ],
            "highlights": _highlights(frame),
        },
        "suppression": {
            **suppression_metadata(),
            **indicator_meta["suppression"],
            "labels": indicator_meta["suppression_labels"],
        },
        "data_quality": {
            "municipality_count": int(len(frame)),
            "department_count": int(frame["departamento_codigo"].nunique()),
            "join_status": "340 de 340 códigos municipales únicos; sin códigos descartados.",
            "crosswalk": meta_2030,
            "projection_overlap": overlap,
            "reference_catalog": meta_2035,
            "mineduc_2022": {
                "establishments": meta_establishments,
                "students": meta_students,
            },
            "vital_events_2025": {
                "births": meta_births,
                "deaths": meta_deaths,
            },
            "segeplan": {
                "poverty_2023": meta_poverty,
                "allocation_2026": meta_allocation,
            },
        },
        "sources": sources,
        "limitations": LIMITATIONS,
    }

    indicators_json = out_dir / "indicators.json"
    _write_json(indicators_json, payload)

    provenance = {
        "snapshot_id": SNAPSHOT_ID,
        "generated_at_utc": generated_at,
        "verified_on": VERIFIED_ON,
        "note": (
            "Manifiesto de procedencia. Cada archivo crudo se registra con URL "
            "exacta, fecha UTC, SHA-256 y bytes. Los archivos existentes se "
            "reutilizan sin volver a descargarse."
        ),
        "files": sources,
        "transformations": {
            "reference_catalog": {
                **meta_2035,
                "derivation": (
                    "Se extrajeron las 340 filas municipales de la hoja "
                    "'Resultado Municipal' y se normalizaron los códigos a 4 dígitos."
                ),
                "output": "data/reference/municipios_gt_340.csv",
            },
            "projections_2030": meta_2030,
            "projection_overlap": overlap,
            "births_2025": meta_births,
            "deaths_2025": meta_deaths,
            "establishments_2022": meta_establishments,
            "students_2022": meta_students,
            "poverty_2023": meta_poverty,
            "allocation_2026": meta_allocation,
            "indicators": {
                "rows": int(len(frame)),
                "columns": int(len(frame.columns)),
                "suppression": indicator_meta["suppression"],
                "pressure_classes": indicator_meta["pressure_classes"],
            },
        },
    }

    outputs = {}
    for path in [
        out_dir / "municipios.parquet",
        out_dir / "indicators.parquet",
        indicators_json,
        reference_path,
    ]:
        outputs[path.as_posix()] = {
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
    provenance["outputs"] = outputs
    provenance_json = out_dir / "provenance.json"
    _write_json(provenance_json, provenance)

    # Mirror the two JSON files used by the static frontend.
    web_public = Path(web_public) if web_public else None
    if web_public:
        _copy_if_changed(indicators_json, web_public / "indicators.json")
        _copy_if_changed(provenance_json, web_public / "provenance.json")

    summary = {
        "municipalities": int(len(frame)),
        "departments": int(frame["departamento_codigo"].nunique()),
        "suppressed_cells": indicator_meta["suppression"]["total_suppressed_cells"],
        "downloaded": [
            record["source_id"]
            for record in manifest.get("files", {}).values()
            if record.get("download_status") == "downloaded"
        ],
        "outputs": outputs,
        "web_public": str(web_public) if web_public else None,
        "generated_at_utc": generated_at,
    }
    if verbose:
        print(
            f"Listo: {summary['municipalities']} municipios, "
            f"{summary['departments']} departamentos, "
            f"{summary['suppressed_cells']} celdas suprimidas."
        )
        print(f"JSON: {indicators_json}")
        print(f"Procedencia: {provenance_json}")
        if web_public:
            print(f"Copia para el frontend: {web_public / 'indicators.json'}")
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--out-dir", type=Path, default=Path("data/processed"))
    parser.add_argument(
        "--web-public",
        type=Path,
        default=Path("web/public/data"),
        help="Carpeta pública del frontend; use 'none' para no copiar.",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Falla si falta un archivo en lugar de descargarlo.",
    )
    args = parser.parse_args(argv)
    web_public = None if str(args.web_public).lower() == "none" else args.web_public
    build_all(
        data_dir=args.data_dir,
        out_dir=args.out_dir,
        web_public=web_public,
        skip_download=args.skip_download,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
