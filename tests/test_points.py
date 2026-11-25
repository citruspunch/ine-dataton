from __future__ import annotations

import json

import pytest

from radar.config import WEB_DATA_DIR


def test_point_layer_applies_999_and_coordinate_filters():
    path = WEB_DATA_DIR / "points.json"
    if not path.exists():
        pytest.skip("Salidas no construidas; ejecute `uv run radar build`.")
    payload = json.loads(path.read_text(encoding="utf-8"))
    meta = json.loads((WEB_DATA_DIR / "meta.json").read_text(encoding="utf-8"))
    fields = payload["fields"]
    points = payload["points"]
    idx = {name: position for position, name in enumerate(fields)}

    assert meta["pointLayer"]["source_places"] == 20_036
    assert meta["pointLayer"]["excluded_suffix_999"] == 301
    assert meta["pointLayer"]["excluded_missing_coordinates"] == 313
    assert meta["pointLayer"]["included"] == len(points) == 19_723
    # The 301 "999" places are a subset of the 313 coordinate-less records.
    assert meta["pointLayer"]["excluded_total"] == 313

    for point in points:
        assert not str(point[idx["id"]]).endswith("999")
        assert point[idx["lon"]] is not None
        assert point[idx["lat"]] is not None
        assert -93 < point[idx["lon"]] < -88
        assert 13 < point[idx["lat"]] < 18
