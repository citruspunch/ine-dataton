from __future__ import annotations

import pytest

from pipeline.normalize import (
    GUATEMALA_CROSSWALK,
    apply_guatemala_crosswalk,
    crosswalk_code,
    normalize_department_code,
    normalize_municipio_code,
)


def test_department_and_municipality_normalisation():
    assert normalize_department_code(1) == "01"
    assert normalize_department_code("1.0") == "01"
    assert normalize_department_code("22") == "22"
    assert normalize_municipio_code(101) == "0101"
    assert normalize_municipio_code("101.0") == "0101"
    assert normalize_municipio_code("0101") == "0101"
    assert normalize_municipio_code(1001) == "1001"
    assert normalize_municipio_code(2217) == "2217"


def test_guatemala_crosswalk_covers_the_16_non_capital_municipalities():
    assert len(GUATEMALA_CROSSWALK) == 16
    assert set(GUATEMALA_CROSSWALK) == {f"01{n:02d}" for n in range(23, 39)}
    assert set(GUATEMALA_CROSSWALK.values()) == {f"01{n:02d}" for n in range(2, 18)}

    mapped = []
    for source in range(23, 39):
        code, applied = apply_guatemala_crosswalk("01", f"01{source:02d}")
        assert applied is True
        assert code == f"01{source - 21:02d}"
        mapped.append(code)
    assert len(set(mapped)) == 16


def test_crosswalk_does_not_touch_guatemala_city_or_other_departments():
    assert apply_guatemala_crosswalk("01", "0101") == ("0101", False)
    assert apply_guatemala_crosswalk("02", "0201") == ("0201", False)
    assert apply_guatemala_crosswalk("01", "0139") == ("0139", False)
    assert crosswalk_code("0101") == ("0101", False)
    assert crosswalk_code("0123") == ("0102", True)
    assert crosswalk_code("0138") == ("0117", True)
    assert crosswalk_code("0201") == ("0201", False)


def test_invalid_codes_fail_loudly():
    with pytest.raises(ValueError):
        normalize_municipio_code("")
    with pytest.raises(ValueError):
        normalize_municipio_code("abc")
