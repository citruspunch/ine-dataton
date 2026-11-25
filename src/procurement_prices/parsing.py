"""Number, date and text parsing used by every ingester.

The rules are deliberately explicit and tested: Latin-American price files mix
``1,234.56``, ``3,500.000`` and ``1.234,56``, and the DPIR files contain literal
invalid dates such as ``30/11/-0001``.
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

_EMPTY_TOKENS = {
    "",
    "-",
    "--",
    "---",
    "s/d",
    "sd",
    "sin dato",
    "sin datos",
    "n/a",
    "na",
    "nan",
    "none",
    "null",
    "nat",
    "#n/a",
    "#na",
    "#¡valor!",
}

_MONTHS_ES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "novienbre": 11,  # seen in the 2026 IPMC header
    "diciembre": 12,
    "ene": 1,
    "feb": 2,
    "mar": 3,
    "abr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "ago": 8,
    "sep": 9,
    "sept": 9,
    "oct": 10,
    "nov": 11,
    "dic": 12,
}


def strip_accents(value: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", value) if not unicodedata.combining(char)
    )


def normalize_text(value: Any) -> str:
    """Lowercase, accent-free, punctuation-free text for search keys."""

    if value is None:
        return ""
    text = strip_accents(str(value)).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    text = str(value).replace("\xa0", " ").replace("\u202f", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text or None


def is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return normalize_text(value) in {normalize_text(token) for token in _EMPTY_TOKENS}


def parse_number(raw: Any) -> tuple[float | None, bool]:
    """Parse a price-like value.

    Returns ``(value, had_thousands_separator)``.  The second flag lets the UI
    show a "formato con comas" badge without altering the numeric summary.
    """

    if raw is None:
        return None, False
    if isinstance(raw, bool):
        return None, False
    if isinstance(raw, (int, float)):
        if math.isnan(raw) or math.isinf(raw):
            return None, False
        return float(raw), False

    original = str(raw).strip()
    if original.lower() in _EMPTY_TOKENS or normalize_text(original) in {
        normalize_text(token) for token in _EMPTY_TOKENS
    }:
        return None, False

    had_separator = "," in original
    text = original.replace("\xa0", "").replace("\u202f", "").replace(" ", "")
    text = re.sub(r"[Qq\$]", "", text)
    text = re.sub(r"[^0-9,.\-()]", "", text)

    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()")
    if not text or text in {"-", ".", ","}:
        return None, had_separator
    if text.count("-") > 1 or ("-" in text and not text.startswith("-")):
        return None, had_separator

    if "," in text and "." in text:
        last_comma = text.rfind(",")
        last_dot = text.rfind(".")
        if last_comma > last_dot:
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        groups = text.split(",")
        if len(groups) == 2:
            left, right = groups
            if (
                right.isdigit()
                and len(right) == 3
                and 1 <= len(left.lstrip("-")) <= 3
                and left.lstrip("-") not in {"0", ""}
            ):
                # 1,234 -> 1234 (thousands), 0,123 -> 0.123 (decimal)
                text = text.replace(",", "")
            else:
                text = text.replace(",", ".")
        else:
            # 1,234,567 -> thousands
            if all(part.isdigit() and len(part) == 3 for part in groups[1:]):
                text = text.replace(",", "")
            else:
                return None, had_separator
    elif "." in text:
        groups = text.split(".")
        if len(groups) > 2:
            if all(part.isdigit() and len(part) == 3 for part in groups[1:]):
                text = text.replace(".", "")
            else:
                return None, had_separator
        # single dot is a decimal point in every INE file we ingest

    if negative and not text.startswith("-"):
        text = "-" + text

    try:
        value = float(text)
    except ValueError:
        return None, had_separator
    if not math.isfinite(value):
        return None, had_separator
    return value, had_separator


@dataclass(frozen=True)
class ParsedDate:
    value: date | None
    status: str  # "valid" | "invalid" | "missing"
    raw: str | None

    @property
    def iso(self) -> str | None:
        return self.value.isoformat() if self.value else None


_DATE_DMY = re.compile(r"^(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})$")
_DATE_ISO = re.compile(r"^(\d{4})-(\d{1,2})-(\d{1,2})(?:[T ].*)?$")
_DATE_TEXT = re.compile(r"^(\d{1,2})\s*(?:de\s+)?([a-zA-ZáéíóúÁÉÍÓÚñÑ]+)\s*(?:de\s+)?(\d{4})$")


def parse_month_es(value: Any) -> int | None:
    text = normalize_text(value)
    if not text:
        return None
    return _MONTHS_ES.get(text)


def parse_date(raw: Any) -> ParsedDate:
    """Parse a date without ever inventing one.

    ``30/11/-0001`` is kept verbatim and marked invalid; a missing cell is
    marked missing.  Callers can therefore exclude it from statistics while
    still showing the original value to an auditor.
    """

    if raw is None:
        return ParsedDate(None, "missing", None)
    if isinstance(raw, float) and math.isnan(raw):
        return ParsedDate(None, "missing", None)
    if isinstance(raw, datetime):
        return ParsedDate(raw.date(), "valid", raw.date().isoformat())
    if isinstance(raw, date):
        return ParsedDate(raw, "valid", raw.isoformat())
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        # Excel serial date, only when it is plausibly a date.
        serial = float(raw)
        if 20_000 <= serial <= 80_000:
            value = (datetime(1899, 12, 30) + timedelta(days=serial)).date()
            return ParsedDate(value, "valid", str(raw))
        return ParsedDate(None, "invalid", str(raw))

    text = str(raw).strip()
    if (
        not text
        or text.lower() in _EMPTY_TOKENS
        or normalize_text(text) in {normalize_text(token) for token in _EMPTY_TOKENS}
    ):
        return ParsedDate(None, "missing", text or None)

    cleaned = text.replace("\xa0", " ").strip()

    match = _DATE_ISO.match(cleaned)
    if match:
        year, month, day = (int(part) for part in match.groups())
        return _build_date(year, month, day, text)

    match = _DATE_DMY.match(cleaned)
    if match:
        day, month, year = (int(part) for part in match.groups())
        if year < 100:
            year += 2000
        return _build_date(year, month, day, text)

    match = _DATE_TEXT.match(cleaned)
    if match:
        day = int(match.group(1))
        month = parse_month_es(match.group(2))
        year = int(match.group(3))
        if month is None:
            return ParsedDate(None, "invalid", text)
        return _build_date(year, month, day, text)

    return ParsedDate(None, "invalid", text)


def _build_date(year: int, month: int, day: int, raw: str) -> ParsedDate:
    if not (1900 <= year <= 2100) or not (1 <= month <= 12) or not (1 <= day <= 31):
        return ParsedDate(None, "invalid", raw)
    try:
        return ParsedDate(date(year, month, day), "valid", raw)
    except ValueError:
        return ParsedDate(None, "invalid", raw)


def month_start(year: Any, month: Any) -> date | None:
    try:
        year_i = int(year)
        month_i = int(month)
    except (TypeError, ValueError):
        return None
    if not (1900 <= year_i <= 2100) or not (1 <= month_i <= 12):
        return None
    return date(year_i, month_i, 1)


def truncate(value: str | None, limit: int = 700) -> str | None:
    if value is None:
        return None
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"
