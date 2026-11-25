"""Closed source registry.

Every URL in the application comes from this file. Nothing is discovered at
runtime and no URL is constructed from user input. The registry records the
exact download URL, the dataset landing page, the CKAN license status and the
attribution string that the UI must display.

Sources were verified on 2026-11-23 (America/Guatemala) and downloaded on the
date recorded in ``data/manifest.json`` and ``data/processed/provenance.json``.
"""

from __future__ import annotations

from dataclasses import dataclass


VERIFIED_ON = "2026-11-23"


@dataclass(frozen=True)
class License:
    """License facts as declared by the publisher (or explicitly absent)."""

    id: str
    name: str
    url: str | None
    commercial_use: bool | None
    attribution_required: bool
    ckan_license_id: str | None
    ckan_license_title: str | None
    status: str
    notes: str

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "commercial_use": self.commercial_use,
            "attribution_required": self.attribution_required,
            "ckan_license_id": self.ckan_license_id,
            "ckan_license_title": self.ckan_license_title,
            "status": self.status,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class Source:
    """A single citable data file."""

    id: str
    title: str
    publisher: str
    dataset_page: str
    download_url: str
    filename: str
    format: str
    license: License
    attribution: str
    description: str
    min_bytes: int = 1_000
    expected_magic: bytes | None = None

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "publisher": self.publisher,
            "dataset_page": self.dataset_page,
            "download_url": self.download_url,
            "filename": self.filename,
            "format": self.format,
            "license": self.license.as_dict(),
            "attribution": self.attribution,
            "description": self.description,
            "verified_on": VERIFIED_ON,
        }


# --- License objects -------------------------------------------------------

INE_ODC_BY = License(
    id="odc-by",
    name="Open Data Commons Attribution License (ODC-By)",
    url="http://www.opendefinition.org/licenses/odc-by",
    commercial_use=True,
    attribution_required=True,
    ckan_license_id="odc-by",
    ckan_license_title="Open Data Commons Attribution License",
    status="declared",
    notes=(
        "Licencia declarada por el INE en el catálogo CKAN del conjunto de "
        "proyecciones 2015-2030. Requiere atribución."
    ),
)

INE_CC_BY = License(
    id="cc-by",
    name="Creative Commons Attribution (CC BY)",
    url="http://www.opendefinition.org/licenses/cc-by",
    commercial_use=True,
    attribution_required=True,
    ckan_license_id="cc-by",
    ckan_license_title="Creative Commons Attribution",
    status="declared",
    notes="Licencia declarada por el INE en CKAN para el conjunto de lugares poblados.",
)

INE_NOT_DECLARED = License(
    id="ine-no-declarada",
    name="Licencia no declarada en CKAN; estadísticas públicas del INE",
    url="https://www.ine.gob.gt/",
    commercial_use=None,
    attribution_required=True,
    ckan_license_id=None,
    ckan_license_title=None,
    status="not_declared",
    notes=(
        "El recurso CKAN del INE no tiene license_id. Se cita al INE como "
        "fuente y no se atribuye una licencia abierta que la institución no "
        "haya declarado. Verifique los términos vigentes antes de reutilizar."
    ),
)

INE_NOT_ON_CKAN = License(
    id="ine-fuente-institucional",
    name="Estadística pública del INE; licencia CKAN no declarada en esta página",
    url="https://www.ine.gob.gt/proyecciones/",
    commercial_use=None,
    attribution_required=True,
    ckan_license_id=None,
    ckan_license_title=None,
    status="not_published_on_ckan",
    notes=(
        "El archivo municipal 2015-2035 se publica en el sitio institucional "
        "del INE, no en el catálogo CKAN. No se le atribuye una licencia "
        "abierta distinta de la del portal CKAN del INE."
    ),
)

MINEDUC_CC0 = License(
    id="cc-zero",
    name="Creative Commons CCZero (CC0 1.0)",
    url="http://www.opendefinition.org/licenses/cc-zero",
    commercial_use=True,
    attribution_required=False,
    ckan_license_id="cc-zero",
    ckan_license_title="Creative Commons CCZero",
    status="declared",
    notes=(
        "Licencia CC0 declarada por el Ministerio de Educación en su portal "
        "CKAN. Se cita igualmente al MINEDUC como fuente."
    ),
)

SEGEPLAN_CC_NC = License(
    id="cc-nc",
    name="Creative Commons Atribución-NoComercial 2.0 (CC BY-NC 2.0)",
    url="http://creativecommons.org/licenses/by-nc/2.0/",
    commercial_use=False,
    attribution_required=True,
    ckan_license_id="cc-nc",
    ckan_license_title="Creative Commons Non-Commercial (Cualquiera)",
    status="declared",
    notes=(
        "Licencia CC BY-NC 2.0 declarada por SEGEPLAN en su portal CKAN. "
        "USO NO COMERCIAL ÚNICAMENTE. Se exige atribución a SEGEPLAN. "
        "Cualquier reutilización comercial requiere autorización expresa."
    ),
)


# --- Sources ---------------------------------------------------------------

SOURCES: tuple[Source, ...] = (
    Source(
        id="ine-proyecciones-2035",
        title="Estimaciones y proyecciones de población municipal 2015-2035",
        publisher="Instituto Nacional de Estadística (INE), Guatemala",
        dataset_page="https://www.ine.gob.gt/proyecciones/",
        download_url=(
            "https://www.ine.gob.gt/ine/wp-content/uploads/2020/08/"
            "Estimaciones-y-Proyecciones-Municipales-2015-2035.xlsx"
        ),
        filename="ine_proyecciones_municipales_2015_2035.xlsx",
        format="xlsx",
        license=INE_NOT_ON_CKAN,
        attribution="Instituto Nacional de Estadística (INE), Guatemala",
        description=(
            "Población total municipal al 30 de junio de cada año, 2015-2035. "
            "Actualización 2020 de las estimaciones y proyecciones municipales. "
            "Es la fuente del crecimiento poblacional y del catálogo base de "
            "340 municipios."
        ),
        min_bytes=20_000,
        expected_magic=b"PK",
    ),
    Source(
        id="ine-proyecciones-2030",
        title="Proyecciones de población municipal 2015-2030 por sexo y edad",
        publisher="Instituto Nacional de Estadística (INE), Guatemala",
        dataset_page=(
            "https://datos.ine.gob.gt/dataset/proyecciones-de-poblacion-2015-2030"
        ),
        download_url=(
            "https://datos.ine.gob.gt/dataset/23bbe8f8-ec9b-49c9-bcca-de78bec4efc0/"
            "resource/56b97bc0-5624-408d-a136-3931dd05610a/download/"
            "estimaciones-y-proyecciones-de-la-poblacion-total-por-municipio-"
            "segun-sexo-y-edad.-2015-2030.xlsx"
        ),
        filename="ine_proyecciones_municipales_2015_2030.xlsx",
        format="xlsx",
        license=INE_ODC_BY,
        attribution="Instituto Nacional de Estadística (INE), Guatemala",
        description=(
            "Proyecciones municipales 2015-2030 desagregadas por sexo y edad. "
            "Se usa para validar el traslape 2015-2030 y para documentar la "
            "llave +21 de los 16 municipios del departamento de Guatemala."
        ),
        min_bytes=1_000_000,
        expected_magic=b"PK",
    ),
    Source(
        id="ine-nacimientos-2025",
        title="Nacimientos registrados en 2025",
        publisher="Instituto Nacional de Estadística (INE), Guatemala",
        dataset_page=(
            "https://datos.ine.gob.gt/dataset/estadisticas-vitales-nacimientos"
        ),
        download_url=(
            "https://datos.ine.gob.gt/dataset/96888fc0-5ced-4a58-bfd0-2a6a292e3208/"
            "resource/b6847c70-a0b9-4cfd-a405-4ea4360905d7/download/nacimientos_2025.xlsx"
        ),
        filename="ine_nacimientos_2025.xlsx",
        format="xlsx",
        license=INE_NOT_DECLARED,
        attribution="Instituto Nacional de Estadística (INE), Guatemala",
        description=(
            "Microdatos de nacimientos registrados en 2025. Se agregan por "
            "departamento y municipio de residencia de la madre (Deprem/Muprem)."
        ),
        min_bytes=1_000_000,
        expected_magic=b"PK",
    ),
    Source(
        id="ine-defunciones-2025",
        title="Defunciones registradas en 2025",
        publisher="Instituto Nacional de Estadística (INE), Guatemala",
        dataset_page=(
            "https://datos.ine.gob.gt/dataset/estadisticas-vitales-defunciones"
        ),
        download_url=(
            "https://datos.ine.gob.gt/dataset/14f547c3-ad37-4ea1-9e74-16a3ed50ff54/"
            "resource/43adb351-0a14-4783-8401-e5ef21a2222e/download/defunciones_2025.xlsx"
        ),
        filename="ine_defunciones_2025.xlsx",
        format="xlsx",
        license=INE_NOT_DECLARED,
        attribution="Instituto Nacional de Estadística (INE), Guatemala",
        description=(
            "Microdatos de defunciones registradas en 2025. Se agregan por "
            "departamento y municipio de residencia del fallecido (Dredif/MreDif). "
            "Incluye defunciones de menores de 5 años para el ejercicio de "
            "supresión de celdas pequeñas."
        ),
        min_bytes=500_000,
        expected_magic=b"PK",
    ),
    Source(
        id="mineduc-establecimientos-2022",
        title="Establecimientos educativos 2021-2022",
        publisher="Ministerio de Educación (MINEDUC), Guatemala",
        dataset_page=(
            "https://datosabiertos.mineduc.gob.gt/dataset/"
            "6daf991d-59fc-4f2c-a64c-35759ee6cba0"
        ),
        download_url=(
            "https://datosabiertos.mineduc.gob.gt/dataset/"
            "6daf991d-59fc-4f2c-a64c-35759ee6cba0/resource/"
            "b7377ce0-0c66-4f8c-89d7-fd52fc7ab47b/download/"
            "establecimientos_2021-2022.csv"
        ),
        filename="mineduc_establecimientos_2021_2022.csv",
        format="csv",
        license=MINEDUC_CC0,
        attribution="Ministerio de Educación (MINEDUC), Guatemala",
        description=(
            "Directorio de establecimientos educativos con ubicación, sector y "
            "nivel. Se cuenta el número de establecimientos únicos por municipio "
            "en el ciclo 2022."
        ),
        min_bytes=1_000_000,
    ),
    Source(
        id="mineduc-estudiantes-2022",
        title="Estudiantes 2021-2022 por municipio, nivel y sexo",
        publisher="Ministerio de Educación (MINEDUC), Guatemala",
        dataset_page=(
            "https://datosabiertos.mineduc.gob.gt/dataset/"
            "4d947596-0b42-4a9a-b151-53d74b230dd5"
        ),
        download_url=(
            "https://datosabiertos.mineduc.gob.gt/dataset/"
            "4d947596-0b42-4a9a-b151-53d74b230dd5/resource/"
            "3774793e-1c80-4b6a-a0d8-6dca91e51c0a/download/"
            "estudiantes_2021-2022.csv"
        ),
        filename="mineduc_estudiantes_2021_2022.csv",
        format="csv",
        license=MINEDUC_CC0,
        attribution="Ministerio de Educación (MINEDUC), Guatemala",
        description=(
            "Matrícula inscrita por municipio, nivel, grado, sector y etnia en "
            "el ciclo 2022. Se suma InscritosTotal por municipio."
        ),
        min_bytes=500_000,
    ),
    Source(
        id="segeplan-pobreza-2023",
        title="Mapa de pobreza por municipio 2023",
        publisher="Secretaría de Planificación y Programación de la Presidencia (SEGEPLAN)",
        dataset_page=(
            "https://datos.segeplan.gob.gt/dataset/bfddf2e8-db9b-408f-b2b6-2519e207b150"
        ),
        download_url=(
            "https://datos.segeplan.gob.gt/dataset/"
            "bfddf2e8-db9b-408f-b2b6-2519e207b150/resource/"
            "40ccb784-5f6d-47ab-8343-342fa2caabeb/download/"
            "datos-abiertos_resultados-mapa2023_mupio.csv"
        ),
        filename="segeplan_pobreza_municipal_2023.csv",
        format="csv",
        license=SEGEPLAN_CC_NC,
        attribution="SEGEPLAN, Mapas de pobreza a nivel municipal 2023",
        description=(
            "Incidencia de pobreza general y extrema, brecha, severidad y "
            "consumo promedio per cápita por municipio, 2023. La pobreza extrema "
            "no está disponible para 23 municipios."
        ),
        min_bytes=10_000,
    ),
    Source(
        id="segeplan-asignacion-2026",
        title="Cálculo matemático de la asignación constitucional 2026",
        publisher="Secretaría de Planificación y Programación de la Presidencia (SEGEPLAN)",
        dataset_page=(
            "https://datos.segeplan.gob.gt/dataset/f4ee4102-b724-4617-8343-95a03e7fe34b"
        ),
        download_url=(
            "https://datos.segeplan.gob.gt/dataset/"
            "f4ee4102-b724-4617-8343-95a03e7fe34b/resource/"
            "8df77811-4e24-4fe8-af78-6e40153850f8/download/"
            "calculo-matematico-para-la-asignacion-constitucional-a-las-"
            "municipalidades-del-ano-2026.csv"
        ),
        filename="segeplan_asignacion_constitucional_2026.csv",
        format="csv",
        license=SEGEPLAN_CC_NC,
        attribution="SEGEPLAN, Cálculo matemático de la asignación constitucional 2026",
        description=(
            "Distribución del situado constitucional a las 340 municipalidades "
            "para el ejercicio fiscal 2026, con población 2025, ingresos propios "
            "per cápita y número de aldeas y caseríos."
        ),
        min_bytes=10_000,
    ),
)


SOURCE_BY_ID = {source.id: source for source in SOURCES}


def source_ids() -> list[str]:
    return [source.id for source in SOURCES]
