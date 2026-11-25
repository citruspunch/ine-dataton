"""Transform INE spreadsheets into aggregated, static JSON.

Design rules enforced here:

* the 2024 cross-section is stored separately from the 2021–2022 series;
* every DINESE record is mapped to one of the 340 canonical municipalities;
* only establishment counts are published (no firm IDs, no employment);
* populated places ending in 999 or without coordinates never reach map points.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd

from . import __version__
from .catalog import DINESE_SOURCES, SOURCE_BY_KEY, SOURCES
from .fetch import (
    DEFAULT_PROVENANCE_PATH,
    DEFAULT_RAW_DIR,
    PROJECT_ROOT,
    sha256_file,
    utc_now,
    verify_hashes,
)
from .schema import (
    AGE_GROUPS,
    CENSUS_AGE_COLUMNS,
    CIIU_BY_NAME,
    CIIU_SECTIONS,
    SIZE_ORDER,
    VIEW_SERIES,
    VIEW_SNAPSHOT,
    build_notices,
)

DEFAULT_OUT_DIR = PROJECT_ROOT / "web" / "public" / "data"
EXPECTED_MUNICIPALITIES = 340
EXPECTED_DEPARTMENTS = 22
EXPECTED_PLACES = 20_036
EXPECTED_DINESE_ROWS = {2021: 312_923, 2022: 313_272, 2024: 645_431}
EXPECTED_LEGAL_CATEGORIES = {2021: 30, 2022: 29, 2024: 15}
CIIU_KEYS = [letter for letter, _, _ in CIIU_SECTIONS]

LEGAL_SHORT_LABELS = {
    "Individual": "Individual",
    "Sociedad anónima": "Sociedad anónima",
    "Copropiedad de empresa": "Copropiedad de empresa",
    "Copropiedad de bienes": "Copropiedad de bienes",
    "Sociedad de responsabilidad limitada": "S. de responsabilidad limitada",
    "Sociedad civil con fines lucrativos": "Sociedad civil",
    "Sucursal empresa extranjera": "Sucursal extranjera",
    "Contrato de participación": "Contrato de participación",
    "Empresa extranjera inscrita en el país": "Empresa extranjera",
    "Sociedad colectiva": "Sociedad colectiva",
    "Sociedad de emprendimiento": "Sociedad de emprendimiento",
    "Sociedad en comandita por acciones": "Comandita por acciones",
    "Universidad privada": "Universidad privada",
    "Sociedad en comandita simple": "Comandita simple",
    "Sociedad de alianzas para el desarrollo de infraestructura económica": "Alianzas APP",
    "Asociación, fundación, institución religiosa y otra": "Asociación o fundación",
    "Cooperativa": "Cooperativa",
    "Fideicomiso": "Fideicomiso",
    "Bien administrado por fideicomiso": "Bien en fideicomiso",
    "Entidad del estado": "Entidad del Estado",
    "Condominio, propiedad horizontal y similares": "Condominio",
    "Otro tipo de organización legal": "Otra organización legal",
    "Municipalidad": "Municipalidad",
    "Partido politico": "Partido político",
    "Junta escolar, coeduca y similares": "Junta escolar",
    "Centros educativos publicos y comunitarios": "Centro educativo público",
    "Sindicato": "Sindicato",
    "Organizaciones comunitarias": "Organización comunitaria",
    "Misión diplomática y organismo internacional": "Misión diplomática",
    "Sociedad en comandita por acciones ": "Comandita por acciones",
    "Patrimonio hereditario indiviso": "Patrimonio hereditario",
    "Extranjero diplomático o agente de organismo internacional": "Diplomático extranjero",
    "Sociedad de alianzas para el desarrollo de infraestructura económica ": "Alianzas APP",
    "Club deportivo": "Club deportivo",
}


def normalize_name(value: object) -> str:
    """Accent-, case- and punctuation-insensitive key for name matching."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]", "", text)


def _to_int(value: object) -> int:
    if value is None:
        return 0
    if isinstance(value, str):
        value = value.strip().replace(",", "")
        if value in {"", "-", "—"}:
            return 0
    number = pd.to_numeric(value, errors="coerce")
    if pd.isna(number):
        return 0
    return int(round(float(number)))


def _number_series(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.strip()
        .replace({"": "0", "-": "0", "nan": "0", "None": "0"})
        .pipe(pd.to_numeric, errors="coerce")
        .fillna(0)
        .round()
        .astype("int64")
    )


def canonical_code(department_code: int, municipality_code: int) -> str:
    """Build the canonical 4-digit code: 2 dept digits + 2 municipality digits."""
    return f"{int(department_code):02d}{int(municipality_code) % 100:02d}"


def read_census(path: Path) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name="A1_2", header=None, skiprows=6)
    if raw.shape[1] < 30:
        raise RuntimeError(f"{path.name}: se esperaban 30 columnas en el Cuadro A1.2")
    raw = raw.iloc[:, :30]
    raw.columns = [
        "dept_code",
        "department",
        "mun_code",
        "municipality",
        "total",
        "men",
        "women",
        *CENSUS_AGE_COLUMNS,
        "urban",
        "rural",
    ]
    raw = raw.dropna(subset=["dept_code", "mun_code", "municipality", "total"]).copy()
    raw["dept_code"] = raw["dept_code"].map(_to_int)
    raw["mun_code"] = raw["mun_code"].map(_to_int)
    for column in ("total", "men", "women", "urban", "rural", *CENSUS_AGE_COLUMNS):
        raw[column] = _number_series(raw[column])
    raw["municipality"] = raw["municipality"].astype(str).str.strip()
    raw["department"] = raw["department"].astype(str).str.strip()
    raw["code"] = [
        canonical_code(d, m) for d, m in zip(raw["dept_code"], raw["mun_code"])
    ]

    if len(raw) != EXPECTED_MUNICIPALITIES:
        raise RuntimeError(
            f"{path.name}: se esperaban {EXPECTED_MUNICIPALITIES} municipios, hay {len(raw)}"
        )
    if raw["code"].nunique() != EXPECTED_MUNICIPALITIES:
        raise RuntimeError("Los códigos municipales canónicos no son únicos (340/340)")
    if raw["department"].nunique() != EXPECTED_DEPARTMENTS:
        raise RuntimeError(
            f"Se esperaban {EXPECTED_DEPARTMENTS} departamentos, hay "
            f"{raw['department'].nunique()}"
        )
    return raw.sort_values("code").reset_index(drop=True)


def read_places(path: Path) -> pd.DataFrame:
    raw = pd.read_excel(path, header=None, skiprows=6)
    if raw.shape[1] < 8:
        raise RuntimeError(f"{path.name}: se esperaban 8 columnas de lugares poblados")
    raw = raw.iloc[:, :8]
    raw.columns = [
        "dept_code",
        "department",
        "mun_code",
        "municipality",
        "place_code",
        "place",
        "lon",
        "lat",
    ]
    raw = raw.dropna(subset=["dept_code", "mun_code", "place_code", "place"]).copy()
    raw["dept_code"] = raw["dept_code"].map(_to_int)
    raw["mun_code"] = raw["mun_code"].map(_to_int)
    raw["place_code"] = raw["place_code"].map(_to_int)
    raw["place"] = raw["place"].astype(str).str.strip()
    raw["lon"] = pd.to_numeric(raw["lon"], errors="coerce")
    raw["lat"] = pd.to_numeric(raw["lat"], errors="coerce")
    raw["code"] = [
        canonical_code(d, m) for d, m in zip(raw["dept_code"], raw["mun_code"])
    ]
    raw["place_id"] = raw["place_code"].astype(str)
    raw["suffix_999"] = raw["place_code"] % 1000 == 999
    raw["missing_coordinates"] = raw["lon"].isna() | raw["lat"].isna()
    raw["excluded"] = raw["suffix_999"] | raw["missing_coordinates"]

    if len(raw) != EXPECTED_PLACES:
        raise RuntimeError(
            f"{path.name}: se esperaban {EXPECTED_PLACES:,} lugares poblados, hay {len(raw):,}"
        )
    return raw.reset_index(drop=True)


def _counts(values: Iterable[str]) -> dict[str, int]:
    return dict(Counter(values))


def read_dinese(
    path: Path, year: int, pair_to_code: dict[tuple[str, str], str]
) -> dict:
    columns = [
        "SECCION_CIIU_4",
        "TIPO_PERSONERIA",
        "CLA_RANGO_VENTAS",
        "NOMBRE_DEPARTAMENTO",
        "NOMBRE_MUNICIPIO",
    ]
    frame = pd.read_excel(path, dtype=str, usecols=columns)
    frame = frame.fillna("")
    for column in columns:
        frame[column] = frame[column].astype(str).str.strip()

    if len(frame) != EXPECTED_DINESE_ROWS[year]:
        raise RuntimeError(
            f"{path.name}: se esperaban {EXPECTED_DINESE_ROWS[year]:,} registros, "
            f"hay {len(frame):,}"
        )

    unknown_sections = sorted(set(frame["SECCION_CIIU_4"]) - set(CIIU_BY_NAME))
    if unknown_sections:
        raise RuntimeError(f"Secciones CIIU desconocidas en {year}: {unknown_sections}")
    unknown_sizes = sorted(set(frame["CLA_RANGO_VENTAS"]) - set(SIZE_ORDER))
    if unknown_sizes:
        raise RuntimeError(f"Tamaños desconocidos en {year}: {unknown_sizes}")
    if (frame["TIPO_PERSONERIA"] == "").any():
        raise RuntimeError(f"{year}: hay registros sin tipo de personería")

    pair_keys = list(
        zip(
            frame["NOMBRE_DEPARTAMENTO"].map(normalize_name),
            frame["NOMBRE_MUNICIPIO"].map(normalize_name),
        )
    )
    codes = [pair_to_code.get(key) for key in pair_keys]
    missing = sorted({key for key, code in zip(pair_keys, codes) if code is None})
    if missing:
        raise RuntimeError(
            f"{year}: {len(missing)} pares departamento-municipio no están en el "
            f"nomenclador 340/340: {missing[:5]}"
        )
    frame["code"] = codes

    national = {
        "total": int(len(frame)),
        "ciiu": _counts(
            CIIU_BY_NAME[value]["letter"] for value in frame["SECCION_CIIU_4"]
        ),
        "size": _counts(frame["CLA_RANGO_VENTAS"]),
        "legal": _counts(frame["TIPO_PERSONERIA"]),
    }
    national["ciiu"] = {key: national["ciiu"].get(key, 0) for key in CIIU_KEYS}
    national["size"] = {key: national["size"].get(key, 0) for key in SIZE_ORDER}

    legal_order = sorted(
        national["legal"], key=lambda key: (-national["legal"][key], key)
    )
    if len(legal_order) != EXPECTED_LEGAL_CATEGORIES[year]:
        raise RuntimeError(
            f"{year}: se esperaban {EXPECTED_LEGAL_CATEGORIES[year]} categorías de "
            f"personería, hay {len(legal_order)}"
        )

    per_municipality_total = frame.groupby("code").size().to_dict()
    per_ciiu = (
        frame.assign(
            letter=frame["SECCION_CIIU_4"].map(lambda x: CIIU_BY_NAME[x]["letter"])
        )
        .groupby(["code", "letter"])
        .size()
        .to_dict()
    )
    per_size = frame.groupby(["code", "CLA_RANGO_VENTAS"]).size().to_dict()
    per_legal = frame.groupby(["code", "TIPO_PERSONERIA"]).size().to_dict()

    municipalities: dict[str, dict] = {}
    for code in sorted(per_municipality_total):
        municipalities[code] = {
            "total": int(per_municipality_total[code]),
            "ciiu": {
                letter: int(per_ciiu.get((code, letter), 0)) for letter in CIIU_KEYS
            },
            "size": {size: int(per_size.get((code, size), 0)) for size in SIZE_ORDER},
            "legal": {
                label: int(per_legal.get((code, label), 0)) for label in legal_order
            },
        }

    return {
        "year": year,
        "source_key": f"dinese_{year}",
        "total": int(len(frame)),
        "national": national,
        "municipalities": municipalities,
        "legal_order": legal_order,
        "legal_short_labels": {
            label: LEGAL_SHORT_LABELS.get(label, label) for label in legal_order
        },
        "ciiu_active_sections": sum(
            1 for value in national["ciiu"].values() if value > 0
        ),
    }


def _share(part: int, whole: int) -> float | None:
    if not whole:
        return None
    return round(part / whole * 100, 1)


def build_population(row: pd.Series) -> dict:
    ages = [_to_int(row[column]) for column in CENSUS_AGE_COLUMNS]
    total = _to_int(row["total"])
    under_15 = sum(ages[:3])
    working_age = sum(ages[3:13])
    over_64 = sum(ages[13:])
    return {
        "total": total,
        "men": _to_int(row["men"]),
        "women": _to_int(row["women"]),
        "urban": _to_int(row["urban"]),
        "rural": _to_int(row["rural"]),
        "age_groups": [
            {"label": label, "count": count} for label, count in zip(AGE_GROUPS, ages)
        ],
        "age_summary": {
            "under_15": under_15,
            "working_age": working_age,
            "over_64": over_64,
            "under_15_share": _share(under_15, total),
            "working_age_share": _share(working_age, total),
            "over_64_share": _share(over_64, total),
            "urban_share": _share(_to_int(row["urban"]), total),
        },
    }


def build_places(frame: pd.DataFrame) -> dict:
    total = int(len(frame))
    suffix_999 = int(frame["suffix_999"].sum())
    missing_coords = int(frame["missing_coordinates"].sum())
    excluded = int(frame["excluded"].sum())

    items = []
    for row in frame.itertuples(index=False):
        reasons = []
        if row.suffix_999:
            reasons.append("sufijo_999")
        if row.missing_coordinates:
            reasons.append("sin_coordenadas")
        items.append(
            {
                "code": row.place_id,
                "name": row.place,
                "lon": None if pd.isna(row.lon) else round(float(row.lon), 6),
                "lat": None if pd.isna(row.lat) else round(float(row.lat), 6),
                "excluded": bool(row.excluded),
                "reasons": reasons,
            }
        )

    return {
        "total": total,
        "map_points": total - excluded,
        "excluded": {
            "suffix_999": suffix_999,
            "missing_coordinates": missing_coords,
            "union": excluded,
            "both": int((frame["suffix_999"] & frame["missing_coordinates"]).sum()),
        },
        "items": items,
    }


def _rank(values: dict[str, int]) -> dict[str, int]:
    ordered = sorted(values.items(), key=lambda item: (-item[1], item[0]))
    ranks: dict[str, int] = {}
    previous_value = None
    previous_rank = 0
    for position, (code, value) in enumerate(ordered, start=1):
        if value != previous_value:
            previous_rank = position
            previous_value = value
        ranks[code] = previous_rank
    return ranks


def _json_dump(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    )
    path.write_text(text + "\n", encoding="utf-8")


def build(
    raw_dir: Path | str = DEFAULT_RAW_DIR,
    out_dir: Path | str = DEFAULT_OUT_DIR,
    *,
    provenance: dict | None = None,
    provenance_path: Path | str = DEFAULT_PROVENANCE_PATH,
) -> dict:
    """Build all JSON artifacts and return the manifest."""
    raw_dir = Path(raw_dir)
    out_dir = Path(out_dir)

    if provenance is None:
        from .fetch import load_provenance

        provenance = load_provenance(provenance_path)

    files = provenance.get("files", [])
    if not files:
        raise RuntimeError(
            "No hay manifiesto de procedencia. Ejecuta "
            "`uv run municipal-profile fetch` antes de construir."
        )
    digests = verify_hashes(raw_dir, provenance)

    census = read_census(raw_dir / SOURCE_BY_KEY["censo_a1"].filename)
    places = read_places(raw_dir / SOURCE_BY_KEY["lugares_poblados"].filename)

    pair_to_code = {
        (normalize_name(row.department), normalize_name(row.municipality)): row.code
        for row in census.itertuples(index=False)
    }
    if len(pair_to_code) != EXPECTED_MUNICIPALITIES:
        raise RuntimeError(
            "El nomenclador departamento-municipio no tiene 340 pares únicos"
        )

    dinese = {
        source.year: read_dinese(raw_dir / source.filename, source.year, pair_to_code)
        for source in DINESE_SOURCES
    }

    for year, payload in dinese.items():
        if set(payload["municipalities"]) != set(census["code"]):
            raise RuntimeError(
                f"{year}: los municipios DINESE no coinciden con el Censo 2018"
            )

    if set(places["code"]) != set(census["code"]):
        missing_places = sorted(set(places["code"]) - set(census["code"]))
        raise RuntimeError(
            f"Hay lugares poblados con códigos fuera del nomenclador: {missing_places[:5]}"
        )

    age_total = census[list(CENSUS_AGE_COLUMNS)].sum(axis=1)
    if not (age_total == census["total"]).all():
        raise RuntimeError(
            "La suma de grupos de edad no coincide con la población total"
        )
    if not (census["men"] + census["women"] == census["total"]).all():
        raise RuntimeError("Hombres + mujeres no coincide con la población total")
    if not (census["urban"] + census["rural"] == census["total"]).all():
        raise RuntimeError("Urbana + rural no coincide con la población total")

    totals = {year: payload["national"]["total"] for year, payload in dinese.items()}
    legal_counts = {
        year: len(payload["national"]["legal"]) for year, payload in dinese.items()
    }

    places_by_code = {
        code: group.sort_values("place_id").copy()
        for code, group in places.groupby("code")
    }

    national_population = {
        "total": int(census["total"].sum()),
        "men": int(census["men"].sum()),
        "women": int(census["women"].sum()),
        "urban": int(census["urban"].sum()),
        "rural": int(census["rural"].sum()),
        "age_groups": [
            {"label": label, "count": int(census[column].sum())}
            for label, column in zip(AGE_GROUPS, CENSUS_AGE_COLUMNS)
        ],
    }

    legal_series_union = sorted(
        set(dinese[2021]["national"]["legal"]) | set(dinese[2022]["national"]["legal"]),
        key=lambda label: (
            -(
                dinese[2021]["national"]["legal"].get(label, 0)
                + dinese[2022]["national"]["legal"].get(label, 0)
            ),
            label,
        ),
    )
    legal_labels = {
        "2021": dinese[2021]["legal_order"],
        "2022": dinese[2022]["legal_order"],
        "2024": dinese[2024]["legal_order"],
        "series": legal_series_union,
    }
    legal_short = dict(LEGAL_SHORT_LABELS)
    for label in legal_series_union:
        legal_short.setdefault(label, label)

    ranks = {
        year: _rank(
            {code: value["total"] for code, value in payload["municipalities"].items()}
        )
        for year, payload in dinese.items()
    }

    municipalities_list = []
    for row in census.itertuples(index=False):
        municipalities_list.append(
            {
                "code": row.code,
                "name": row.municipality,
                "department_code": f"{int(row.dept_code):02d}",
                "department_name": row.department,
                "population": int(row.total),
                "establishments": {
                    str(year): payload["municipalities"][row.code]["total"]
                    for year, payload in dinese.items()
                },
                "ranks": {str(year): ranks[year][row.code] for year in dinese},
            }
        )

    departments = (
        census[["dept_code", "department"]]
        .drop_duplicates()
        .sort_values("dept_code")
        .assign(
            code=lambda frame: frame["dept_code"].map(
                lambda value: f"{int(value):02d}"
            ),
            municipality_count=lambda frame: frame["dept_code"].map(
                census.groupby("dept_code").size()
            ),
        )
    )
    departments_payload = [
        {
            "code": row.code,
            "name": row.department,
            "municipality_count": int(row.municipality_count),
        }
        for row in departments.itertuples(index=False)
    ]

    # --- profiles -------------------------------------------------------
    profiles_dir = out_dir / "profiles"
    if profiles_dir.exists():
        shutil.rmtree(profiles_dir)
    profiles_dir.mkdir(parents=True, exist_ok=True)

    for row in census.itertuples(index=False):
        code = row.code
        profile = {
            "code": code,
            "name": row.municipality,
            "department_code": f"{int(row.dept_code):02d}",
            "department_name": row.department,
            "population": build_population(pd.Series(row._asdict())),
            "snapshot_2024": {
                "year": 2024,
                "total": dinese[2024]["municipalities"][code]["total"],
                "ciiu": dinese[2024]["municipalities"][code]["ciiu"],
                "size": dinese[2024]["municipalities"][code]["size"],
                "legal": dinese[2024]["municipalities"][code]["legal"],
            },
            "series_2021_2022": {
                "years": [2021, 2022],
                "2021": {
                    "year": 2021,
                    "total": dinese[2021]["municipalities"][code]["total"],
                    "ciiu": dinese[2021]["municipalities"][code]["ciiu"],
                    "size": dinese[2021]["municipalities"][code]["size"],
                    "legal": dinese[2021]["municipalities"][code]["legal"],
                },
                "2022": {
                    "year": 2022,
                    "total": dinese[2022]["municipalities"][code]["total"],
                    "ciiu": dinese[2022]["municipalities"][code]["ciiu"],
                    "size": dinese[2022]["municipalities"][code]["size"],
                    "legal": dinese[2022]["municipalities"][code]["legal"],
                },
            },
            "places": build_places(places_by_code.get(code, places.iloc[0:0])),
        }
        _json_dump(profiles_dir / f"{code}.json", profile)

    # --- meta -----------------------------------------------------------
    notices = build_notices(totals, legal_counts)
    views = [
        {
            "id": VIEW_SNAPSHOT,
            "label": "2024 Snapshot (DINESE 2024 + Census 2018)",
            "label_es": "Corte 2024 (DINESE 2024 + Censo 2018)",
            "short_label": "Corte 2024",
            "dinese_years": [2024],
            "total_establishments": totals[2024],
            "legal_categories": legal_counts[2024],
            "notice": notices["2024"],
        },
        {
            "id": VIEW_SERIES,
            "label": "2021–2022 Series (DINESE 2021–2022 + Census 2018)",
            "label_es": "Serie 2021–2022 (DINESE 2021–2022 + Censo 2018)",
            "short_label": "Serie 2021–2022",
            "dinese_years": [2021, 2022],
            "total_establishments": {str(year): totals[year] for year in (2021, 2022)},
            "legal_categories": {
                str(year): legal_counts[year] for year in (2021, 2022)
            },
            "notice": notices["series"],
        },
    ]

    meta = {
        "schema_version": 1,
        "generated_at_utc": utc_now(),
        "pipeline_version": __version__,
        "title": "Perfil de demanda municipal y actividad económica",
        "subtitle": "Censo 2018 + DINESE 2021, 2022 y 2024 para los 340 municipios",
        "census_year": 2018,
        "views": views,
        "notices": notices,
        "ciiu_sections": [
            {"letter": letter, "name": name, "short": short}
            for letter, name, short in CIIU_SECTIONS
        ],
        "size_order": list(SIZE_ORDER),
        "legal_categories": legal_labels,
        "legal_short_labels": legal_short,
        "national": {
            "population": national_population,
            "dinese": {
                str(year): {
                    **payload["national"],
                    "legal_order": payload["legal_order"],
                }
                for year, payload in dinese.items()
            },
        },
        "coverage": {
            "municipalities": int(len(census)),
            "departments": int(census["department"].nunique()),
            "crosswalk": f"{len(census)}/{EXPECTED_MUNICIPALITIES}",
            "dinese_pairs": {
                str(year): f"{len(payload['municipalities'])}/{EXPECTED_MUNICIPALITIES}"
                for year, payload in dinese.items()
            },
            "dinese_records": {str(year): totals[year] for year in totals},
            "dinese_ciiu_sections": 21,
            "places_total": int(len(places)),
            "places_map_points": int((~places["excluded"]).sum()),
            "places_excluded_suffix_999": int(places["suffix_999"].sum()),
            "places_excluded_missing_coordinates": int(
                places["missing_coordinates"].sum()
            ),
            "places_excluded_union": int(places["excluded"].sum()),
        },
        "sources": files,
        "limitations": [
            "El Censo 2018 es la única base poblacional; no se extrapola a 2024.",
            "DINESE cuenta establecimientos registrados, no empleo, ventas ni personas trabajadoras.",
            "No se publican identificadores de empresa ni microdatos; solo conteos agregados.",
            "2024 es un corte transversal: cobertura y personería no son comparables con 2021–2022.",
            "Las coordenadas son centroides de lugares poblados del Censo 2018; no son direcciones de empresas.",
            "Los lugares con sufijo 999 o sin coordenadas se excluyen de los puntos del mapa.",
        ],
        "definitions": {
            "establishment": (
                "Registro incluido en DINESE para un municipio y año. No implica que el "
                "establecimiento esté operando ni que tenga asalariados."
            ),
            "size": (
                "Rango de ventas declarado en DINESE (Micro, Pequeña, Mediana, Grande). "
                "No es número de empleados."
            ),
            "legal_status": (
                "Tipo de personería tal como lo codifica DINESE en cada año; las categorías "
                "cambian entre 2021–2022 y 2024."
            ),
        },
        "provenance_manifest": "manifest.json",
    }
    _json_dump(out_dir / "meta.json", meta)
    _json_dump(
        out_dir / "municipalities.json",
        {
            "generated_at_utc": meta["generated_at_utc"],
            "departments": departments_payload,
            "municipalities": sorted(
                municipalities_list, key=lambda item: item["code"]
            ),
        },
    )

    # --- manifest -------------------------------------------------------
    output_files = []
    for path in sorted(out_dir.rglob("*.json")):
        if path.name == "manifest.json":
            continue
        output_files.append(
            {
                "path": str(path.relative_to(out_dir)),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )

    manifest = {
        "schema_version": 1,
        "generated_at_utc": meta["generated_at_utc"],
        "pipeline": {
            "name": "municipal-demand-profile",
            "version": __version__,
        },
        "separation": {
            "snapshot": {
                "id": VIEW_SNAPSHOT,
                "years": [2024],
                "profile_key": "snapshot_2024",
                "note": "Corte transversal; no se calculan variaciones contra 2021–2022.",
            },
            "series": {
                "id": VIEW_SERIES,
                "years": [2021, 2022],
                "profile_key": "series_2021_2022",
                "note": "Serie corta comparable solo entre 2021 y 2022.",
            },
        },
        "privacy": {
            "aggregation_level": (
                "municipio × sección CIIU; municipio × tamaño; municipio × personería"
            ),
            "contains_firm_ids": False,
            "contains_employment": False,
            "contains_microdata": False,
            "statistical_secrecy": (
                "Solo conteos agregados. No se exponen identificadores de establecimientos, "
                "nombres de empresas ni personas. Decreto-Ley 3-85."
            ),
        },
        "inputs": [
            {**entry, "build_sha256": digests.get(entry["key"])} for entry in files
        ],
        "counts": meta["coverage"],
        "outputs": output_files,
        "notice": (
            "manifest.json no se incluye a sí mismo en outputs; los demás JSON se "
            "enumeran con tamaño y SHA-256."
        ),
    }
    _json_dump(out_dir / "manifest.json", manifest)
    return manifest


def build_all(
    raw_dir: Path | str = DEFAULT_RAW_DIR,
    out_dir: Path | str = DEFAULT_OUT_DIR,
    *,
    provenance_path: Path | str = DEFAULT_PROVENANCE_PATH,
) -> dict:
    from .fetch import ensure_sources

    provenance = ensure_sources(raw_dir=raw_dir, provenance_path=provenance_path)
    return build(raw_dir, out_dir, provenance=provenance)
