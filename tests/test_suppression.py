from __future__ import annotations

import json
from pathlib import Path

import pytest

from radar.config import WEB_DATA_DIR
from radar.suppress import make_cell


def _walk(node, path="root"):
    if isinstance(node, dict):
        if node.get("suppressed") is True:
            assert "count" not in node, f"count expuesto en {path}"
            assert "rate" not in node, f"rate expuesto en {path}"
        for key, value in node.items():
            _walk(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            _walk(value, f"{path}[{index}]")


def test_suppression_removes_both_count_and_rate():
    cell = make_cell(4, 10_000, 5)
    assert cell == {"suppressed": True, "threshold": 5}
    assert "count" not in cell and "rate" not in cell


def test_zero_cells_are_also_suppressed():
    cell = make_cell(0, 10_000, 5)
    assert cell["suppressed"] is True
    assert set(cell) == {"suppressed", "threshold"}


def test_public_cell_has_rate():
    cell = make_cell(5, 10_000, 5)
    assert cell["suppressed"] is False
    assert cell["count"] == 5
    assert cell["rate"] == 5.0


def test_homicide_threshold_is_ten():
    assert make_cell(9, 50_000, 10)["suppressed"] is True
    assert make_cell(10, 50_000, 10)["suppressed"] is False


@pytest.mark.parametrize(
    "filename",
    ["indicators.json", "death-causes.json", "age-profile.json"],
)
def test_exported_data_never_exposes_suppressed_values(filename: str):
    path = WEB_DATA_DIR / filename
    if not path.exists():
        pytest.skip("Salidas no construidas; ejecute `uv run radar build`.")
    payload = json.loads(path.read_text(encoding="utf-8"))
    _walk(payload)


def test_suppressed_municipality_has_no_derivable_rate():
    path = WEB_DATA_DIR / "indicators.json"
    if not path.exists():
        pytest.skip("Salidas no construidas; ejecute `uv run radar build`.")
    payload = json.loads(path.read_text(encoding="utf-8"))
    fatalities = payload["topics"]["road_safety"]["metrics"]["fatalities"]["criteria"][
        "occurrence"
    ]["levels"]["municipality"]["cells"]
    suppressed = {
        code: cell for code, cell in fatalities.items() if cell.get("suppressed")
    }
    assert suppressed, "La prueba necesita al menos una celda suprimida."
    for cell in suppressed.values():
        assert "count" not in cell and "rate" not in cell
