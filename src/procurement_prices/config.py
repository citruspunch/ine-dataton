"""Static configuration: paths, official dataset registry and provenance metadata.

Every URL in this module points at an official Instituto Nacional de Estadística
(INE) host.  The downloader never invents a URL: it walks the ``urls`` tuple in
order and records which one actually served a valid file.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
PROVENANCE_DIR = DATA_DIR / "provenance"
WEB_DATA_DIR = ROOT / "web" / "data"

DOWNLOADS_MANIFEST = PROVENANCE_DIR / "downloads.json"

#: CKAN hosts seen in the INE open-data portal.
CKAN = "https://datos.ine.gob.gt"
INE_WEB = "https://www.ine.gob.gt"

PRIVACY_NOTE = (
    "Salidas agregadas y de observación. No se incluyen nombres de proveedores, "
    "postores ni identificadores de empresas. Los campos de entidad requirente del "
    "DPIR se omiten deliberadamente; no se intenta reidentificar a ninguna persona, "
    "hogar o empresa."
)

AI_DISCLOSURE = (
    "Se utilizaron asistentes de código con IA generativa durante el desarrollo. "
    "Las decisiones de limpieza, las reglas de calidad y las cifras se verifican con "
    "pruebas automatizadas y revisión humana; consulte el README."
)


@dataclass(frozen=True)
class SourceSpec:
    """One raw file and the provenance needed to audit it."""

    id: str
    group: str
    title: str
    filename: str
    urls: tuple[str, ...]
    source_page: str
    kind: str
    publisher: str
    license_id: str
    license_title: str
    license_url: str | None
    status: str
    coverage: str
    notes: str
    ckan_modified: str | None = None
    ckan_package: str | None = None
    dictionary: bool = False

    @property
    def path(self) -> Path:
        return RAW_DIR / self.filename


DPIR_LICENSE = {
    "id": "odc-by",
    "title": "Open Data Commons Attribution License (ODC-BY)",
    "url": "http://www.opendefinition.org/licenses/odc-by",
}
CC_BY_LICENSE = {
    "id": "cc-by",
    "title": "Creative Commons Attribution (CC-BY)",
    "url": "http://www.opendefinition.org/licenses/cc-by",
}
UNDECLARED_LICENSE = {
    "id": "not-declared",
    "title": "Licencia no declarada en el portal al momento de la descarga",
    "url": None,
}

# The INE WordPress site serves uploads from /ine/wp-content/.  The shorter
# /wp-content/ path is kept as a fallback because it is the public link shown on
# some pages; the downloader validates the magic bytes, so an HTML CAPTCHA page
# is never accepted as a spreadsheet.
HISTORICO_URLS = (
    f"{INE_WEB}/ine/wp-content/uploads/2026/11/HISTORICO-OCTUBRE.xlsx",
    f"{INE_WEB}/wp-content/uploads/2026/11/HISTORICO-OCTUBRE.xlsx",
)
ICC_URLS = (
    f"{INE_WEB}/ine/wp-content/uploads/2026/11/Historico-ICC_VSB_OCTUBRE..xlsx",
    f"{INE_WEB}/wp-content/uploads/2026/11/Historico-ICC_VSB_OCTUBRE..xlsx",
)

_BASE = f"{CKAN}/dataset"
DPIR_PACKAGE = f"{_BASE}/b247b9ac-e95f-4c32-acd3-fc4bdfb6185a"
IPMC_PACKAGE = f"{_BASE}/b45673c0-6227-4469-ad7a-c956392fd058"
CBA_PACKAGE = f"{_BASE}/0317e7b9-9563-4a9c-800f-c74473103063"


SOURCES: dict[str, SourceSpec] = {
    "dpir-2022": SourceSpec(
        id="dpir-2022",
        group="DPIR",
        title="Precios de Referencia — corte junio 2022",
        filename="base-de-datos-pr-actualizados-hasta-junio-2022.csv",
        urls=(
            f"{DPIR_PACKAGE}/resource/aec255ce-11f0-4d6c-90d2-af41b1a49870/download/"
            "base-de-datos-pr-actualizados-hasta-junio-2022.csv",
        ),
        source_page=f"{CKAN}/dataset/precios-de-referencia",
        kind="csv",
        publisher="INE — Departamento de Análisis de Precios",
        status="frozen",
        coverage="Instantánea de precios de referencia observados en compras públicas hasta junio 2022. No es una serie mensual continua.",
        notes="Archivo CKAN congelado. La mayoría de sus registros se repiten en el archivo 2023; se marcan como duplicados y no entran en los resúmenes. Cuando el archivo 2023 perdió el NOG, se conserva la copia 2022 completa.",
        ckan_modified="2023-10-05T20:57:34Z",
        ckan_package="precios-de-referencia",
        license_id=DPIR_LICENSE["id"],
        license_title=DPIR_LICENSE["title"],
        license_url=DPIR_LICENSE["url"],
    ),
    "dpir-2023": SourceSpec(
        id="dpir-2023",
        group="DPIR",
        title="Precios de Referencia — corte agosto 2023",
        filename="precios-de-referencia-al-02102023.xlsx",
        urls=(
            f"{DPIR_PACKAGE}/resource/d2c5d27a-a4e1-4263-9f3a-10b344884d28/download/"
            "precios-de-referencia-al-02102023.xlsx",
        ),
        source_page=f"{CKAN}/dataset/precios-de-referencia",
        kind="xlsx",
        publisher="INE — Departamento de Análisis de Precios",
        status="frozen",
        coverage="Instantánea de precios de referencia hasta agosto 2023. Es la fuente preferente cuando un registro también aparece en el archivo 2022.",
        notes="Archivo publicado como 'Precios de Referencia - Septiembre 2023'; el último dato válido observado es del 4 de agosto de 2023.",
        ckan_modified="2023-10-05T20:57:13Z",
        ckan_package="precios-de-referencia",
        license_id=DPIR_LICENSE["id"],
        license_title=DPIR_LICENSE["title"],
        license_url=DPIR_LICENSE["url"],
    ),
    "dpir-dictionary": SourceSpec(
        id="dpir-dictionary",
        group="DPIR",
        title="Diccionario de Precios de Referencia",
        filename="diccionario-pr.xlsx",
        urls=(
            f"{DPIR_PACKAGE}/resource/024bd9b2-9fb0-45c8-9635-0056f81dd6b0/download/"
            "diccionario-pr.xlsx",
        ),
        source_page=f"{CKAN}/dataset/precios-de-referencia",
        kind="xlsx",
        publisher="INE — Departamento de Análisis de Precios",
        status="frozen",
        coverage="Diccionario de variables del DPIR (junio 2022).",
        notes="Se usa para mostrar las definiciones de los campos; no aporta observaciones de precios.",
        ckan_modified="2022-09-19T18:44:11Z",
        ckan_package="precios-de-referencia",
        license_id=DPIR_LICENSE["id"],
        license_title=DPIR_LICENSE["title"],
        license_url=DPIR_LICENSE["url"],
        dictionary=True,
    ),
    "ipmc-history": SourceSpec(
        id="ipmc-history",
        group="IPMC",
        title="IPMC — histórico de 89 materiales",
        filename="HISTORICO-OCTUBRE.xlsx",
        urls=HISTORICO_URLS,
        source_page=f"{INE_WEB}/indice-de-materiales-de-construccion/",
        kind="xlsx",
        publisher="INE — Sección de Otros Índices y Precios Sectoriales",
        status="current",
        coverage="89 materiales y servicios, base diciembre 2018 = 100. Índice simple no ponderado; cobertura Región I Metropolitana y municipios seleccionados.",
        notes="El archivo se publica mensualmente en el sitio del INE. El corte se lee de la última columna mensual con dato, no del nombre del archivo.",
        ckan_modified="2026-11-23T17:41:19Z",
        ckan_package="indice-de-precios-de-materiales-de-construccion-ipmc",
        license_id=CC_BY_LICENSE["id"],
        license_title=CC_BY_LICENSE["title"],
        license_url=CC_BY_LICENSE["url"],
    ),
    "icc-2026": SourceSpec(
        id="icc-2026",
        group="ICC",
        title="ICC Vivienda Social Básica — 2026",
        filename="Historico-ICC_VSB_OCTUBRE..xlsx",
        urls=ICC_URLS,
        source_page=f"{INE_WEB}/indice-de-costos/",
        kind="xlsx",
        publisher="INE — Índice de Costos de Construcción",
        status="limited",
        coverage="Solo 2026 (enero–octubre) y Región I. Índice encadenado con período de referencia 2025 = 100; no es un precio de mercado.",
        notes="El ICC es un índice de costos de una vivienda social básica (materiales, mano de obra, herramienta y equipo), no un precio de un insumo individual.",
        license_id=UNDECLARED_LICENSE["id"],
        license_title=UNDECLARED_LICENSE["title"],
        license_url=None,
    ),
    "cbau-percapita": SourceSpec(
        id="cbau-percapita",
        group="BASKETS",
        title="CBA Urbana — costo per cápita 2024–2026",
        filename="costo-cba-percapita_u.xlsx",
        urls=(
            f"{CBA_PACKAGE}/resource/6721d034-7af0-4622-ae34-be10f0f2ac89/download/"
            "costo-cba-percapita_u.xlsx",
        ),
        source_page=f"{CKAN}/dataset/costos-de-la-cba-urbana-y-rural",
        kind="xlsx",
        publisher="INE — Departamento de Estadísticas de Precios",
        status="limited",
        coverage="Costo diario y mensual por persona de la Canasta Básica Alimentaria urbana, 2024–2026.",
        notes="Costo de la canasta, no precio de un producto individual. La ventana histórica disponible empieza en 2024.",
        ckan_modified="2026-11-09T17:51:38Z",
        ckan_package="costos-de-la-cba-urbana-y-rural",
        license_id=UNDECLARED_LICENSE["id"],
        license_title=UNDECLARED_LICENSE["title"],
        license_url=None,
    ),
    "cbar-percapita": SourceSpec(
        id="cbar-percapita",
        group="BASKETS",
        title="CBA Rural — costo per cápita 2024–2026",
        filename="costo-cba-percapita_r.xlsx",
        urls=(
            f"{CBA_PACKAGE}/resource/69abf503-56da-4de5-9017-875009394843/download/"
            "costo-cba-percapita_r.xlsx",
        ),
        source_page=f"{CKAN}/dataset/costos-de-la-cba-urbana-y-rural",
        kind="xlsx",
        publisher="INE — Departamento de Estadísticas de Precios",
        status="limited",
        coverage="Costo diario y mensual por persona de la Canasta Básica Alimentaria rural, 2024–2026.",
        notes="Costo de la canasta, no precio de un producto individual. La ventana histórica disponible empieza en 2024.",
        ckan_modified="2026-11-09T17:50:46Z",
        ckan_package="costos-de-la-cba-urbana-y-rural",
        license_id=UNDECLARED_LICENSE["id"],
        license_title=UNDECLARED_LICENSE["title"],
        license_url=None,
    ),
    "cbau-history": SourceSpec(
        id="cbau-history",
        group="BASKETS",
        title="CBA Urbana — grupos y productos 2024–2026",
        filename="historico-cbau_es_2024-2026.xlsx",
        urls=(
            f"{CBA_PACKAGE}/resource/595747ff-a866-4192-99fa-fc032a7795b7/download/"
            "historico-cbau_es_2024-2026.xlsx",
        ),
        source_page=f"{CKAN}/dataset/costos-de-la-cba-urbana-y-rural",
        kind="xlsx",
        publisher="INE — Departamento de Estadísticas de Precios",
        status="limited",
        coverage="Costo por grupo alimenticio y por producto de la CBA urbana, 2024–2026.",
        notes="El precio por unidad base se deriva de la cantidad base y el costo; es un precio implícito de la canasta, no una cotización de mercado independiente.",
        ckan_modified="2026-11-09T17:52:11Z",
        ckan_package="costos-de-la-cba-urbana-y-rural",
        license_id=UNDECLARED_LICENSE["id"],
        license_title=UNDECLARED_LICENSE["title"],
        license_url=None,
    ),
    "cbar-history": SourceSpec(
        id="cbar-history",
        group="BASKETS",
        title="CBA Rural — grupos y productos 2024–2026",
        filename="historico-cbar_es_2024-2026.xlsx",
        urls=(
            f"{CBA_PACKAGE}/resource/23cf94ba-25e9-457b-87fd-a5c7c1e92bcd/download/"
            "historico-cbar_es_2024-2026.xlsx",
        ),
        source_page=f"{CKAN}/dataset/costos-de-la-cba-urbana-y-rural",
        kind="xlsx",
        publisher="INE — Departamento de Estadísticas de Precios",
        status="limited",
        coverage="Costo por grupo alimenticio y por producto de la CBA rural, 2024–2026.",
        notes="El precio por unidad base se deriva de la cantidad base y el costo; es un precio implícito de la canasta, no una cotización de mercado independiente.",
        ckan_modified="2026-11-09T17:50:46Z",
        ckan_package="costos-de-la-cba-urbana-y-rural",
        license_id=UNDECLARED_LICENSE["id"],
        license_title=UNDECLARED_LICENSE["title"],
        license_url=None,
    ),
}


GROUP_META: dict[str, dict[str, str]] = {
    "DPIR": {
        "label": "Precios de Referencia",
        "shortLabel": "DPIR",
        "tagline": "Precios observados en compras públicas",
        "description": (
            "Precios de referencia registrados por el INE a partir de operaciones de compra "
            "pública. Se usan como banda orientativa antes de cotizar; no son una serie "
            "mensual continua."
        ),
        "statusLabel": "Serie congelada",
        "accent": "teal",
    },
    "IPMC": {
        "label": "Materiales de construcción",
        "shortLabel": "IPMC",
        "tagline": "Índice de precios de 89 materiales",
        "description": (
            "Índice de Precios de Materiales de Construcción, base diciembre 2018 = 100. "
            "Mide variación de precios de 89 materiales y servicios; no es un precio en quetzales."
        ),
        "statusLabel": "Mensual · Región I",
        "accent": "ochre",
    },
    "ICC": {
        "label": "Costo de construcción",
        "shortLabel": "ICC",
        "tagline": "Índice de costos de vivienda social",
        "description": (
            "Índice de Costos de Construcción de la Vivienda Social Básica, referencia 2025 = 100. "
            "Solo 2026 y Región I; combina materiales, mano de obra, herramienta y equipo."
        ),
        "statusLabel": "Parcial · 2026 · Región I",
        "accent": "clay",
    },
    "BASKETS": {
        "label": "Canastas básicas",
        "shortLabel": "CBAU / CBAR",
        "tagline": "Costo de la canasta alimentaria",
        "description": (
            "Costo per cápita y por producto de la Canasta Básica Alimentaria urbana y rural. "
            "La ventana disponible es 2024–2026; el costo de canasta no es un precio de mercado individual."
        ),
        "statusLabel": "Ventana 2024–2026",
        "accent": "olive",
    },
}

SOURCE_GROUP_ORDER = ("DPIR", "IPMC", "ICC", "BASKETS")
