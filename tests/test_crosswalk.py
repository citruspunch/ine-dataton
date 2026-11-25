from __future__ import annotations

import csv
from pathlib import Path

import pytest

from radar.config import REFERENCE_DIR
from radar.normalize import crosswalk_census_to_projection


def test_crosswalk_has_340_unique_municipalities():
    with (REFERENCE_DIR / "municipios_crosswalk.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    codes = [row["code"] for row in rows]
    assert len(codes) == 340
    assert len(set(codes)) == 340
    assert len({row["dept_code"] for row in rows}) == 22
    assert len({row["geo_shape_id"] for row in rows}) == 340


def test_guatemala_crosswalk_is_exactly_plus_21():
    census_codes = [f"01{n:02d}" for n in range(2, 18)]
    projected = [crosswalk_census_to_projection(code) for code in census_codes]
    assert projected == [f"01{n + 21:02d}" for n in range(2, 18)]
    assert len(set(projected)) == 16
    assert crosswalk_census_to_projection("0101") == "0101"
    assert crosswalk_census_to_projection("0123") == "0123"  # idempotent
    assert crosswalk_census_to_projection("2217") == "2217"


def test_crosswalk_matches_projection_universe():
    import pandas as pd

    path = REFERENCE_DIR.parent / "raw" / "proyecciones_poblacion_2015_2030.xlsx"
    if not path.exists():
        pytest.skip("Proyecciones no descargadas; ejecute `uv run radar build`.")
    frame = pd.read_excel(path, dtype=str)
    projection_codes = set(frame["MUPIO"].str.zfill(4))
    with (REFERENCE_DIR / "municipios_crosswalk.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert {row["code"] for row in rows} == projection_codes
    assert len(projection_codes) == 340
