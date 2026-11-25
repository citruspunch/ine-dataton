"""Statistical secrecy helpers.

A suppressed cell must not carry a count or a rate. Rates are just as
disclosable as counts when the population denominator is public, so both
fields are omitted for cells below the threshold.
"""

from __future__ import annotations

from typing import Any

from .config import RATE_BASE


def make_cell(count: int, population: int, threshold: int) -> dict[str, Any]:
    """Return a public cell or a suppression marker.

    Zero counts are also suppressed because the PRD states that any cell with
    fewer than five cases must be suppressed.
    """

    if count < 0:
        raise ValueError("Los conteos no pueden ser negativos.")
    if population <= 0:
        raise ValueError("El denominador poblacional debe ser positivo.")
    if count < threshold:
        return {"suppressed": True, "threshold": threshold}
    return {
        "suppressed": False,
        "count": int(count),
        "rate": round(count / population * RATE_BASE, 2),
        "threshold": threshold,
    }


def make_count_cell(count: int, threshold: int) -> dict[str, Any]:
    """A count-only cell for age bands.

    Age bands use the total municipal population as denominator elsewhere, so a
    "rate" for a band would be misleading. The age profile therefore publishes
    counts only, suppressed with the same rules.
    """

    if count < 0:
        raise ValueError("Los conteos no pueden ser negativos.")
    if count < threshold:
        return {"suppressed": True, "threshold": threshold}
    return {"suppressed": False, "count": int(count), "threshold": threshold}


def make_empty(reason: str) -> dict[str, Any]:
    return {"available": False, "reason": reason}


def is_public(cell: dict[str, Any]) -> bool:
    return not cell.get("suppressed", False)
