"""Territorial code normalisation and the +21 crosswalk."""

from __future__ import annotations

import math
import re
from typing import Any, Iterable

import pandas as pd

from .config import GUATEMALA_CROSSWALK_OFFSET


def clean_code(value: Any) -> str | None:
    """Turn Excel's numeric casualties (``107``, ``107.0``) into ``'0107'``."""

    if value is None:
        return None
    if isinstance(value, float):
        if math.isnan(value):
            return None
        value = int(value)
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "na", "n/a"}:
        return None
    if re.fullmatch(r"\d+\.0+", text):
        text = text.split(".")[0]
    digits = re.sub(r"\D", "", text)
    if not digits:
        return None
    return digits


def normalize_municipality(value: Any) -> str | None:
    """Normalise a municipality code to four digits.

    The INE event files mix three-digit codes (``107``) with four-digit codes
    (``0107``). Codes such as ``999`` or ``9999`` mean "unknown" and are not
    territories.
    """

    digits = clean_code(value)
    if not digits:
        return None
    if len(digits) > 4 and digits.startswith("0"):
        digits = digits[-4:]
    if len(digits) > 4:
        return None
    code = digits.zfill(4)
    if code in {"0999", "9999", "0000"}:
        return None
    return code


def crosswalk_census_to_projection(code: str) -> str:
    """Apply the +21 crosswalk for the 16 Guatemala department municipalities.

    Census 2018 uses 0101–0117. The 2015–2030 projections keep 0101 (Guatemala
    City) and renumber 0102–0117 as 0123–0138. The remaining 324 municipalities
    keep their code. Calling this function twice must not double-shift a code,
    which is guaranteed by only accepting the census range.
    """

    code = str(code).zfill(4)
    if not code.startswith("01") or code == "0101":
        return code
    number = int(code)
    if 102 <= number <= 117:
        return f"{number + GUATEMALA_CROSSWALK_OFFSET:04d}"
    return code


def canonical_municipality(value: Any) -> str | None:
    """Normalise then crosswalk a municipality code to the projection coding."""

    code = normalize_municipality(value)
    if code is None:
        return None
    return crosswalk_census_to_projection(code)


def canonical_series(values: pd.Series) -> pd.Series:
    """Vectorised version of :func:`canonical_municipality`."""

    return values.map(canonical_municipality)


def department_of(municipality: str) -> str:
    return municipality[:2]


def valid_department(code: Any) -> str | None:
    digits = clean_code(code)
    if not digits:
        return None
    code = digits.zfill(2)
    if 1 <= int(code) <= 22:
        return code
    return None


def assert_340(codes: Iterable[str]) -> None:
    unique = set(codes)
    if len(unique) != 340:
        raise ValueError(f"Se esperaban 340 municipios y se encontraron {len(unique)}.")
