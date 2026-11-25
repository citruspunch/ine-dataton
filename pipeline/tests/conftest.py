"""Fixtures compartidas: se trabaja con los archivos oficiales ya cacheados."""

from __future__ import annotations

from pathlib import Path

import pytest

from ine_basket.cba import load_cba
from ine_basket.ipc import (
    build_ipc_monthly,
    read_general_index_base_2023,
    read_general_index_base_2024,
    read_splice,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "data" / "raw"

URBAN_COSTS = RAW_DIR / "costo-cba-percapita_u.xlsx"
RURAL_COSTS = RAW_DIR / "costo-cba-percapita_r.xlsx"
URBAN_PRODUCTS = RAW_DIR / "historico-cbau_es_2024-2026.xlsx"
RURAL_PRODUCTS = RAW_DIR / "historico-cbar_es_2024-2026.xlsx"
IPC_2023 = RAW_DIR / "ipc_2024_datosabiertos.xls"
IPC_2024 = RAW_DIR / "base-de-datos-ipc-ano-2025_es.xls"
IPC_SPLICE = RAW_DIR / "ipc_emprepu_es25.xlsx"


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def raw_dir() -> Path:
    missing = [
        path.name
        for path in (
            URBAN_COSTS,
            RURAL_COSTS,
            URBAN_PRODUCTS,
            RURAL_PRODUCTS,
            IPC_2023,
            IPC_2024,
            IPC_SPLICE,
        )
        if not path.exists()
    ]
    if missing:
        pytest.skip(f"Faltan archivos fuente en data/raw: {missing}")
    return RAW_DIR


@pytest.fixture(scope="session")
def urban(raw_dir: Path):
    return load_cba(URBAN_COSTS, URBAN_PRODUCTS, "Urbana")


@pytest.fixture(scope="session")
def rural(raw_dir: Path):
    return load_cba(RURAL_COSTS, RURAL_PRODUCTS, "Rural")


@pytest.fixture(scope="session")
def ipc(raw_dir: Path):
    return build_ipc_monthly(
        read_general_index_base_2023(IPC_2023),
        read_general_index_base_2024(IPC_2024),
        read_splice(IPC_SPLICE),
    )
