"""Paths, official sources and analysis constants."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.environ.get("RADAR_DATA_DIR", PROJECT_ROOT / "data"))
RAW_DIR = DATA_DIR / "raw"
REFERENCE_DIR = DATA_DIR / "reference"
PROCESSED_DIR = DATA_DIR / "processed"
WEB_DATA_DIR = Path(
    os.environ.get("RADAR_WEB_DATA_DIR", PROJECT_ROOT / "web" / "public" / "data")
)

DATA_YEAR = 2025
POPULATION_YEAR = 2025
RATE_BASE = 10_000
SUPPRESSION_THRESHOLD = 5
HOMICIDE_SUICIDE_THRESHOLD = 10

#: The 16 municipalities of the Guatemala department that change code between
#: the 2018 census (0102–0117) and the 2015–2030 projections (0123–0138).
GUATEMALA_CROSSWALK_OFFSET = 21

DEPARTMENT_NAMES = {
    "01": "Guatemala",
    "02": "El Progreso",
    "03": "Sacatepéquez",
    "04": "Chimaltenango",
    "05": "Escuintla",
    "06": "Santa Rosa",
    "07": "Sololá",
    "08": "Totonicapán",
    "09": "Quetzaltenango",
    "10": "Suchitepéquez",
    "11": "Retalhuleu",
    "12": "San Marcos",
    "13": "Huehuetenango",
    "14": "Quiché",
    "15": "Baja Verapaz",
    "16": "Alta Verapaz",
    "17": "Petén",
    "18": "Izabal",
    "19": "Zacapa",
    "20": "Chiquimula",
    "21": "Jalapa",
    "22": "Jutiapa",
}


@dataclass(frozen=True)
class Source:
    """An official input file and the provenance we must keep for it."""

    filename: str
    url: str
    kind: str  # "xlsx" | "geojson"
    license: str
    publisher: str


#: Five 2025 event databases plus the population and geography tables.
CORE_SOURCES: tuple[Source, ...] = (
    Source(
        "nacimientos_2025.xlsx",
        "https://datos.ine.gob.gt/dataset/96888fc0-5ced-4a58-bfd0-2a6a292e3208/resource/"
        "b6847c70-a0b9-4cfd-a405-4ea4360905d7/download/nacimientos_2025.xlsx",
        "xlsx",
        "Datos abiertos INE — catálogo sin licencia explícita; se cita la fuente",
        "Instituto Nacional de Estadística (INE), Guatemala",
    ),
    Source(
        "defunciones_2025.xlsx",
        "https://datos.ine.gob.gt/dataset/14f547c3-ad37-4ea1-9e74-16a3ed50ff54/resource/"
        "43adb351-0a14-4783-8401-e5ef21a2222e/download/defunciones_2025.xlsx",
        "xlsx",
        "Datos abiertos INE — catálogo sin licencia explícita; se cita la fuente",
        "Instituto Nacional de Estadística (INE), Guatemala",
    ),
    Source(
        "base-de-datos-hechos-de-transito-pnc-2025.xlsx",
        "https://datos.ine.gob.gt/dataset/1960f9e0-93a2-4e12-9692-8867b8150a54/resource/"
        "dc29a0a2-31b2-49d8-a047-aa9bd6f2afcb/download/"
        "base-de-datos-hechos-de-transito-pnc-2025.xlsx",
        "xlsx",
        "CC BY (INE, a partir de la PNC)",
        "INE, a partir de la Policía Nacional Civil (PNC)",
    ),
    Source(
        "base-de-datos-fallecidos-y-lesionados-pnc-2025.xlsx",
        "https://datos.ine.gob.gt/dataset/b80e7836-a158-4830-9177-bca5a3b6cf0d/resource/"
        "2ffc0ffd-74f5-4cae-bbd8-6fa0698e3492/download/"
        "base-de-datos-fallecidos-y-lesionados-pnc-2025.xlsx",
        "xlsx",
        "CC BY (INE, a partir de la PNC)",
        "INE, a partir de la Policía Nacional Civil (PNC)",
    ),
    Source(
        "base-de-datos-vehiculos-involucrados-pnc-2025.xlsx",
        "https://datos.ine.gob.gt/dataset/a241d504-1c89-49d2-a490-a73cfc21276d/resource/"
        "a157bee0-1e72-448f-8fc7-399ba7b9606d/download/"
        "base-de-datos-vehiculos-involucrados-pnc-2025.xlsx",
        "xlsx",
        "CC BY (INE, a partir de la PNC)",
        "INE, a partir de la Policía Nacional Civil (PNC)",
    ),
    Source(
        "proyecciones_poblacion_2015_2030.xlsx",
        "https://datos.ine.gob.gt/dataset/23bbe8f8-ec9b-49c9-bcca-de78bec4efc0/resource/"
        "56b97bc0-5624-408d-a136-3931dd05610a/download/"
        "estimaciones-y-proyecciones-de-la-poblacion-total-por-municipio-segun-sexo-y-edad.-2015-2030.xlsx",
        "xlsx",
        "ODC-BY (INE)",
        "Instituto Nacional de Estadística (INE), Guatemala",
    ),
    Source(
        "censo_2018_cuadro_a1.xlsx",
        "https://datos.ine.gob.gt/dataset/78019333-d80b-45e8-b694-fb3b8d65e19e/resource/"
        "4b9c7220-ca0c-41a9-a121-348f533b070e/download/"
        "cuadro-a1-poblacion-total-censada-por-sexo-grupos-quinquenales-de-edad-y-area.xlsx",
        "xlsx",
        "CC BY (INE)",
        "Instituto Nacional de Estadística (INE), Guatemala",
    ),
    Source(
        "centroides_lugares_poblados_2018.xlsx",
        "https://datos.ine.gob.gt/dataset/78019333-d80b-45e8-b694-fb3b8d65e19e/resource/"
        "053dfa99-b3f9-4b1f-a99f-fc933ef00da4/download/"
        "centroides-de-lugares-poblados-de-la-republica-de-guatemala.-censo-2018.xlsx",
        "xlsx",
        "CC BY (INE)",
        "Instituto Nacional de Estadística (INE), Guatemala",
    ),
)

#: Municipal and departmental boundaries. The PRD requires a shaded territory
#: map but INE's data bank publishes event and census tables, not polygons, so
#: the pipeline uses the openly licensed OCHA/geoBoundaries geometries.
GEO_SOURCES: tuple[Source, ...] = (
    Source(
        "gtm_adm1.geojson",
        "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/GTM/ADM1/"
        "geoBoundaries-GTM-ADM1_simplified.geojson",
        "geojson",
        "CC BY 3.0 IGO (OCHA FISS / geoBoundaries)",
        "OCHA FISS via geoBoundaries",
    ),
    Source(
        "gtm_adm2.geojson",
        "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/GTM/ADM2/"
        "geoBoundaries-GTM-ADM2_simplified.geojson",
        "geojson",
        "CC BY 3.0 IGO (OCHA FISS / geoBoundaries)",
        "OCHA FISS via geoBoundaries",
    ),
)

ALL_SOURCES: tuple[Source, ...] = CORE_SOURCES + GEO_SOURCES

#: Topic and metric labels shared by the pipeline and the UI.
TOPICS = {
    "road_safety": {
        "label": "Seguridad vial",
        "shortLabel": "Vial",
        "description": "Hechos de tránsito, víctimas y vehículos involucrados registrados por la PNC en 2025.",
    },
    "births": {
        "label": "Nacimientos",
        "shortLabel": "Nacimientos",
        "description": "Nacimientos registrados en Guatemala durante 2025.",
    },
    "deaths": {
        "label": "Defunciones",
        "shortLabel": "Defunciones",
        "description": "Defunciones ocurridas en Guatemala durante 2025, con desglose de causas seleccionadas.",
    },
}

METRIC_LABELS = {
    "incidents": "Hechos de tránsito",
    "fatalities": "Personas fallecidas",
    "injuries": "Personas lesionadas",
    "vehicles": "Vehículos involucrados",
    "births": "Nacimientos",
    "deaths": "Defunciones",
    "homicide": "Homicidios",
    "suicide": "Suicidios",
    "traffic": "Tránsito (V01–V99)",
}

CRITERIA = {
    "residence": "Lugar de residencia",
    "occurrence": "Lugar de ocurrencia",
}
