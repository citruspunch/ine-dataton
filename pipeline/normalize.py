"""Municipal code normalisation and the Guatemala-department +21 crosswalk.

INE files disagree on code width. The wide 2015-2035 table stores Guatemala
City as ``101`` and Quesada as ``2217``; the long 2015-2030 table stores
Guatemala City as ``0101`` but numbers the other 16 municipalities of the
department of Guatemala as ``0123``-``0138``. The current 4-digit catalogue uses
``0101``-``0117``.

The crosswalk is therefore: for department ``01`` only, source suffix 23-38 maps
to catalogue suffix 02-17 (source suffix minus 21). The 16 mapped codes are
exposed as ``GUATEMALA_CROSSWALK`` and are tested explicitly.
"""

from __future__ import annotations

import re

import pandas as pd


GUATEMALA_CROSSWALK: dict[str, str] = {
    f"01{source:02d}": f"01{source - 21:02d}" for source in range(23, 39)
}

# The crosswalk must map to the 16 non-capital municipalities (0102-0117).
assert set(GUATEMALA_CROSSWALK.values()) == {f"01{n:02d}" for n in range(2, 18)}


def _digits(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        raise ValueError("Código vacío")
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    text = re.sub(r"[^0-9]", "", text)
    if not text:
        raise ValueError(f"Código sin dígitos: {value!r}")
    return text


def normalize_department_code(value: object) -> str:
    """Return a 2-digit department code (``1``, ``01`` and ``1.0`` -> ``01``)."""

    digits = _digits(value)
    if len(digits) > 2:
        digits = digits[-2:]
    return digits.zfill(2)


def normalize_municipio_code(value: object) -> str:
    """Return a 4-digit municipal code (``101``, ``101.0`` -> ``0101``)."""

    digits = _digits(value)
    if len(digits) > 4:
        digits = digits[-4:]
    return digits.zfill(4)


def split_code(code: object) -> tuple[str, str]:
    normalized = normalize_municipio_code(code)
    return normalized[:2], normalized[2:]


def apply_guatemala_crosswalk(
    department: object, municipality: object
) -> tuple[str, bool]:
    """Normalise a (department, municipality) pair and apply the +21 crosswalk.

    Returns ``(four_digit_code, crosswalk_applied)``.
    """

    dept = normalize_department_code(department)
    muni = normalize_municipio_code(municipality)
    if dept == "01":
        suffix = int(muni[2:])
        if 23 <= suffix <= 38:
            return f"01{suffix - 21:02d}", True
    return muni, False


def crosswalk_code(code: object) -> tuple[str, bool]:
    """Apply the crosswalk to an already-normalised 4-digit code."""

    normalized = normalize_municipio_code(code)
    if normalized in GUATEMALA_CROSSWALK:
        return GUATEMALA_CROSSWALK[normalized], True
    return normalized, False


def assert_unique_codes(codes: pd.Series, label: str, expected: int = 340) -> None:
    duplicates = codes[codes.duplicated()].tolist()
    if duplicates:
        raise ValueError(f"{label}: códigos duplicados {duplicates[:10]}")
    if len(codes) != expected:
        raise ValueError(f"{label}: se esperaban {expected} códigos, hay {len(codes)}")
    invalid = [code for code in codes if not re.fullmatch(r"\d{4}", str(code))]
    if invalid:
        raise ValueError(f"{label}: códigos con formato inválido {invalid[:10]}")
