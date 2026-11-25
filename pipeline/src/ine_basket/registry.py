"""Catálogo de los archivos oficiales del INE usados por el simulador.

Cada entrada guarda la URL exacta de descarga, los identificadores del catálogo
CKAN (``datos.ine.gob.gt``), el estado de licencia y la fecha de última
modificación reportada por el portal. Esta información se copia al manifiesto
de procedencia que consume la aplicación web.

Verificado contra el portal el 2026-11-24 (UTC).
"""

from __future__ import annotations

from dataclasses import dataclass

CKAN_BASE = "https://datos.ine.gob.gt"


@dataclass(frozen=True, slots=True)
class DatasetSpec:
    key: str
    filename: str
    url: str
    title: str
    role: str
    coverage: str
    package_id: str
    package_name: str
    package_title: str
    resource_id: str
    license_id: str | None
    license_title: str
    license_url: str | None
    resource_last_modified_utc: str
    notes: str = ""

    @property
    def package_url(self) -> str:
        return f"{CKAN_BASE}/dataset/{self.package_id}"

    @property
    def license_status(self) -> str:
        return "declarada" if self.license_id else "no declarada"

    @property
    def extension(self) -> str:
        return self.filename.rsplit(".", 1)[-1].lower()


_CC_BY = {
    "license_id": "cc-by",
    "license_title": "Creative Commons Attribution (CC BY 4.0)",
    "license_url": "http://www.opendefinition.org/licenses/cc-by",
}

CBA_PACKAGE = {
    "package_id": "0317e7b9-9563-4a9c-800f-c74473103063",
    "package_name": "costos-de-la-cba-urbana-y-rural",
    "package_title": "Costos de la CA Urbana y Rural y CBA Urbana y Rural",
    # El conjunto de datos de la CBA no declara licencia en CKAN.
    "license_id": None,
    "license_title": "Sin licencia declarada en el catálogo CKAN (© INE)",
    "license_url": None,
}

IPC_2024_PACKAGE = {
    "package_id": "cfd35c49-2f16-4c85-b74c-d5f43659b7e1",
    "package_name": "indice-de-precios-al-consumidor-base-diciembre-2023-100-0",
    "package_title": "IPC por Producto Base Diciembre 2023 = 100.00",
    **_CC_BY,
}

IPC_2025_PACKAGE = {
    "package_id": "4243818d-b479-4bc1-aae6-2735e2b51265",
    "package_name": "ipc-por-producto-ano-2024-100-0",
    "package_title": "IPC Base Anual 2024=100.00",
    **_CC_BY,
}


DATASETS: tuple[DatasetSpec, ...] = (
    DatasetSpec(
        key="cba_urbana_percapita",
        filename="costo-cba-percapita_u.xlsx",
        url=(
            f"{CKAN_BASE}/dataset/{CBA_PACKAGE['package_id']}/resource/"
            "6721d034-7af0-4622-ae34-be10f0f2ac89/download/costo-cba-percapita_u.xlsx"
        ),
        title="Costo per cápita de la CBA Urbana 2024-2026",
        role="cba-costos",
        coverage="Urbana · 2024-01 a 2026-10",
        resource_id="6721d034-7af0-4622-ae34-be10f0f2ac89",
        resource_last_modified_utc="2026-11-09T17:51:38Z",
        **CBA_PACKAGE,
    ),
    DatasetSpec(
        key="cba_rural_percapita",
        filename="costo-cba-percapita_r.xlsx",
        url=(
            f"{CKAN_BASE}/dataset/{CBA_PACKAGE['package_id']}/resource/"
            "69abf503-56da-4de5-9017-875009394843/download/costo-cba-percapita_r.xlsx"
        ),
        title="Costo per cápita de la CBA Rural 2024-2026",
        role="cba-costos",
        coverage="Rural · 2024-01 a 2026-10",
        resource_id="69abf503-56da-4de5-9017-875009394843",
        resource_last_modified_utc="2026-11-09T17:50:46Z",
        **CBA_PACKAGE,
    ),
    DatasetSpec(
        key="cba_urbana_productos",
        filename="historico-cbau_es_2024-2026.xlsx",
        url=(
            f"{CKAN_BASE}/dataset/{CBA_PACKAGE['package_id']}/resource/"
            "595747ff-a866-4192-99fa-fc032a7795b7/download/historico-cbau_es_2024-2026.xlsx"
        ),
        title="Grupo alimenticio y producto CBA Urbana 2024-2026",
        role="cba-productos",
        coverage="Urbana · 2024-01 a 2026-10",
        resource_id="595747ff-a866-4192-99fa-fc032a7795b7",
        resource_last_modified_utc="2026-11-09T21:18:41Z",
        notes="Hojas 'Histórico grupo alimen CBAU' e 'Histórico producto CBAU'.",
        **CBA_PACKAGE,
    ),
    DatasetSpec(
        key="cba_rural_productos",
        filename="historico-cbar_es_2024-2026.xlsx",
        url=(
            f"{CKAN_BASE}/dataset/{CBA_PACKAGE['package_id']}/resource/"
            "23cf94ba-25e9-457b-87fd-a5c7c1e92bcd/download/historico-cbar_es_2024-2026.xlsx"
        ),
        title="Grupo alimenticio y por producto CBA Rural 2024-2026",
        role="cba-productos",
        coverage="Rural · 2024-01 a 2026-10",
        resource_id="23cf94ba-25e9-457b-87fd-a5c7c1e92bcd",
        resource_last_modified_utc="2026-11-09T17:58:50Z",
        notes="Hojas 'Histórico grupo alimen CBAR' e 'Histórico producto CBAR'.",
        **CBA_PACKAGE,
    ),
    DatasetSpec(
        key="ipc_2024",
        filename="ipc_2024_datosabiertos.xls",
        url=(
            f"{CKAN_BASE}/dataset/{IPC_2024_PACKAGE['package_id']}/resource/"
            "f9878de2-0d4d-4325-95f0-110567303db7/download/ipc_2024_datosabiertos.xls"
        ),
        title="Índice de Precios al Consumidor por Producto 2024",
        role="ipc-serie-base-2023",
        coverage="República · 2024 (base diciembre 2023 = 100)",
        resource_id="f9878de2-0d4d-4325-95f0-110567303db7",
        resource_last_modified_utc="2025-02-17T14:50:25Z",
        notes="Serie con base diciembre 2023 = 100. No se concatena sin empalme.",
        **IPC_2024_PACKAGE,
    ),
    DatasetSpec(
        key="ipc_2025",
        filename="base-de-datos-ipc-ano-2025_es.xls",
        url=(
            f"{CKAN_BASE}/dataset/{IPC_2025_PACKAGE['package_id']}/resource/"
            "4b1c485c-78cb-4a0e-b11e-39306a8647f1/download/"
            "base-de-datos-ipc-ano-2025_es.xls"
        ),
        title="Base de datos IPC 2025-2026",
        role="ipc-serie-base-2024",
        coverage="República · 2025-01 a 2026-10 (base 2024 = 100)",
        resource_id="4b1c485c-78cb-4a0e-b11e-39306a8647f1",
        resource_last_modified_utc="2026-11-09T17:08:34Z",
        notes="Serie con base 2024 = 100. No se concatena sin empalme.",
        **IPC_2025_PACKAGE,
    ),
    DatasetSpec(
        key="ipc_empalme",
        filename="ipc_emprepu_es25.xlsx",
        url=(
            f"{CKAN_BASE}/dataset/{IPC_2025_PACKAGE['package_id']}/resource/"
            "6b2cb40a-188c-47c9-9288-ba11c40b5910/download/ipc_emprepu_es25.xlsx"
        ),
        title="Empalme del IPC por República (base anual 2024 = 100)",
        role="ipc-empalme",
        coverage="República · serie histórica empalmada, 1983 a 2026-10",
        resource_id="6b2cb40a-188c-47c9-9288-ba11c40b5910",
        resource_last_modified_utc="2026-11-09T17:47:24Z",
        notes=(
            "Fuente oficial de las variaciones mensual, acumulada e interanual. "
            "Aplica el factor de enlace entre bases; es la única serie que la app "
            "usa para variaciones del IPC."
        ),
        **IPC_2025_PACKAGE,
    ),
)

DATASETS_BY_KEY: dict[str, DatasetSpec] = {spec.key: spec for spec in DATASETS}
DATASETS_BY_FILENAME: dict[str, DatasetSpec] = {spec.filename: spec for spec in DATASETS}
