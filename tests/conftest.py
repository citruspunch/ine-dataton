from __future__ import annotations

from pathlib import Path

import pytest

from pipeline.build import build_all
from pipeline.sources import SOURCES


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_AVAILABLE = all((DATA_DIR / source.filename).exists() for source in SOURCES)


@pytest.fixture(scope="session")
def built_outputs(tmp_path_factory: pytest.TempPathFactory):
    """Build once against the cached raw files and reuse the outputs."""

    if not RAW_AVAILABLE:
        pytest.skip(
            "Faltan archivos crudos en data/. Ejecute `uv run build-pressure` primero."
        )
    out_dir = tmp_path_factory.mktemp("processed")
    summary = build_all(
        data_dir=DATA_DIR,
        out_dir=out_dir,
        web_public=None,
        skip_download=True,
        verbose=False,
    )
    return summary, out_dir
