"""Authoritative source catalogue for the INE data used by the profile.

All URLs point at the official INE open-data bank (CKAN). The catalogue is
intentionally explicit: the pipeline never guesses a download location, and
the provenance manifest records the exact URL used for every file.
"""

from __future__ import annotations

from dataclasses import dataclass

INE_DATA_BANK = "https://datos.ine.gob.gt"

CC_BY = {
    "license_id": "cc-by",
    "license_title": "Creative Commons Attribution",
    "license_url": "http://www.opendefinition.org/licenses/cc-by",
    "license_status": "Abierta (CKAN: CC BY)",
}


@dataclass(frozen=True)
class Source:
    key: str
    filename: str
    dataset: str
    title: str
    package_id: str
    resource_id: str
    url: str
    year: int
    kind: str
    ckan_metadata_modified: str
    license_id: str = CC_BY["license_id"]
    license_title: str = CC_BY["license_title"]
    license_url: str = CC_BY["license_url"]
    license_status: str = CC_BY["license_status"]

    @property
    def page_url(self) -> str:
        return f"{INE_DATA_BANK}/dataset/{self.package_id}"

    def manifest_entry(self) -> dict:
        return {
            "key": self.key,
            "filename": self.filename,
            "dataset": self.dataset,
            "title": self.title,
            "year": self.year,
            "kind": self.kind,
            "url": self.url,
            "page_url": self.page_url,
            "package_id": self.package_id,
            "resource_id": self.resource_id,
            "ckan_metadata_modified": self.ckan_metadata_modified,
            "license": {
                "id": self.license_id,
                "title": self.license_title,
                "url": self.license_url,
                "status": self.license_status,
            },
        }


_DINESE_PACKAGE = "794d0a7e-6c2b-4c21-809f-f23b8936407c"
_CENSUS_PACKAGE = "78019333-d80b-45e8-b694-fb3b8d65e19e"

DINESE_SOURCES = (
    Source(
        key="dinese_2021",
        filename="dinese-2021.xlsx",
        dataset="Directorio Nacional Estadístico de Empresas (DINESE)",
        title="DINESE 2021 — Empresas 2021",
        package_id=_DINESE_PACKAGE,
        resource_id="d785b230-1933-4fad-9223-cb0d3647ef2e",
        url=(
            "https://datos.ine.gob.gt/dataset/794d0a7e-6c2b-4c21-809f-f23b8936407c/"
            "resource/d785b230-1933-4fad-9223-cb0d3647ef2e/download/dinese-2021.xlsx"
        ),
        year=2021,
        kind="dinese",
        ckan_metadata_modified="2026-03-02T15:31:39.575156",
    ),
    Source(
        key="dinese_2022",
        filename="dinese-2022.xlsx",
        dataset="Directorio Nacional Estadístico de Empresas (DINESE)",
        title="DINESE 2022 — Empresas 2022",
        package_id=_DINESE_PACKAGE,
        resource_id="46d58dea-4529-4486-a5cd-cfc648401b19",
        url=(
            "https://datos.ine.gob.gt/dataset/794d0a7e-6c2b-4c21-809f-f23b8936407c/"
            "resource/46d58dea-4529-4486-a5cd-cfc648401b19/download/dinese-2022.xlsx"
        ),
        year=2022,
        kind="dinese",
        ckan_metadata_modified="2026-03-02T15:32:06.499532",
    ),
    Source(
        key="dinese_2024",
        filename="dinese-2024.xlsx",
        dataset="Directorio Nacional Estadístico de Empresas (DINESE)",
        title="DINESE 2024 — Empresas 2024",
        package_id=_DINESE_PACKAGE,
        resource_id="d6836e3d-c7fe-457b-adbf-26ab462dfb56",
        url=(
            "https://datos.ine.gob.gt/dataset/794d0a7e-6c2b-4c21-809f-f23b8936407c/"
            "resource/d6836e3d-c7fe-457b-adbf-26ab462dfb56/download/dinese-2024.xlsx"
        ),
        year=2024,
        kind="dinese",
        ckan_metadata_modified="2026-03-02T15:33:24.480967",
    ),
)

CENSUS_SOURCES = (
    Source(
        key="censo_a1",
        filename="censo-a1.xlsx",
        dataset="Censo 2018 — Lugares poblados",
        title=(
            "Cuadro A1 — Población total censada por sexo, grupos quinquenales "
            "de edad y área"
        ),
        package_id=_CENSUS_PACKAGE,
        resource_id="4b9c7220-ca0c-41a9-a121-348f533b070e",
        url=(
            "https://datos.ine.gob.gt/dataset/78019333-d80b-45e8-b694-fb3b8d65e19e/"
            "resource/4b9c7220-ca0c-41a9-a121-348f533b070e/download/"
            "cuadro-a1-poblacion-total-censada-por-sexo-grupos-quinquenales-de-edad-y-area.xlsx"
        ),
        year=2018,
        kind="census",
        ckan_metadata_modified="2025-06-11T16:19:42.382242",
    ),
    Source(
        key="lugares_poblados",
        filename="lugares-poblados.xlsx",
        dataset="Censo 2018 — Lugares poblados",
        title=("Listado de lugares poblados — centroides de la República de Guatemala"),
        package_id=_CENSUS_PACKAGE,
        resource_id="053dfa99-b3f9-4b1f-a99f-fc933ef00da4",
        url=(
            "https://datos.ine.gob.gt/dataset/78019333-d80b-45e8-b694-fb3b8d65e19e/"
            "resource/053dfa99-b3f9-4b1f-a99f-fc933ef00da4/download/"
            "centroides-de-lugares-poblados-de-la-republica-de-guatemala.-censo-2018.xlsx"
        ),
        year=2018,
        kind="places",
        ckan_metadata_modified="2025-06-11T16:19:42.382242",
    ),
)

SOURCES = CENSUS_SOURCES + DINESE_SOURCES
SOURCE_BY_KEY = {s.key: s for s in SOURCES}
