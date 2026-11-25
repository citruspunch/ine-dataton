from __future__ import annotations

import json
from pathlib import Path

import pytest

from radar.cli import verify_outputs
from radar.config import WEB_DATA_DIR


@pytest.fixture(scope="module")
def outputs():
    required = [
        "meta.json",
        "territories.json",
        "indicators.json",
        "death-causes.json",
        "points.json",
        "municipios.geojson",
        "departamentos.geojson",
    ]
    if not all((WEB_DATA_DIR / name).exists() for name in required):
        pytest.skip("Salidas no construidas; ejecute `uv run radar build`.")
    return WEB_DATA_DIR


def test_verify_outputs_invariants(outputs):
    result = verify_outputs(outputs)
    assert result["municipalities"] == 340
    assert result["departments"] == 22


def test_geojson_has_all_territories(outputs):
    municipalities = json.loads(
        (outputs / "municipios.geojson").read_text(encoding="utf-8")
    )
    departments = json.loads(
        (outputs / "departamentos.geojson").read_text(encoding="utf-8")
    )
    assert len(municipalities["features"]) == 340
    assert len(departments["features"]) == 22
    codes = {feature["properties"]["code"] for feature in municipalities["features"]}
    assert len(codes) == 340


def test_rates_use_projected_population(outputs):
    territories = json.loads((outputs / "territories.json").read_text(encoding="utf-8"))
    indicators = json.loads((outputs / "indicators.json").read_text(encoding="utf-8"))
    population = {
        row["code"]: row["population"] for row in territories["municipalities"]
    }
    cells = indicators["topics"]["births"]["metrics"]["births"]["criteria"][
        "residence"
    ]["levels"]["municipality"]["cells"]
    checked = 0
    for code, cell in cells.items():
        if cell["suppressed"]:
            continue
        expected = round(cell["count"] / population[code] * 10_000, 2)
        assert abs(cell["rate"] - expected) < 0.011
        checked += 1
    assert checked > 300


def test_every_topic_has_residence_and_occurrence_notes(outputs):
    indicators = json.loads((outputs / "indicators.json").read_text(encoding="utf-8"))
    for topic in indicators["topics"].values():
        for metric in topic["metrics"].values():
            criteria = metric["criteria"]
            assert set(criteria) == {"residence", "occurrence"}
            for key in ("residence", "occurrence"):
                if criteria[key]["available"]:
                    assert criteria[key]["note"]
                else:
                    assert criteria[key]["reason"]


def test_road_safety_does_not_invent_residence(outputs):
    indicators = json.loads((outputs / "indicators.json").read_text(encoding="utf-8"))
    for metric in indicators["topics"]["road_safety"]["metrics"].values():
        assert metric["criteria"]["residence"]["available"] is False
        assert metric["criteria"]["occurrence"]["available"] is True
        assert "PNC" in metric["criteria"]["residence"]["reason"]


def test_vehicle_metadata_is_not_exported(outputs):
    text = (outputs / "indicators.json").read_text(encoding="utf-8").lower()
    assert "marca_veh" not in text
    assert "color_veh" not in text
    assert "modelo_veh" not in text
