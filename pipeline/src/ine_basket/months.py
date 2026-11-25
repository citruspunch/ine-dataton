"""Manejo cronológico de meses en español.

El INE publica los meses como texto (``"Septiembre"``, ``"Octubre"``…). Ordenar
esas etiquetas alfabéticamente coloca ``Septiembre`` después de ``Octubre``, un
error clásico en tableros de datos. Todas las funciones de este módulo traducen
el nombre a un número de mes y ordenan por ``(año, número_de_mes)``.

También se rechazan periodos anteriores a 2024 porque la CBA 2024-2026
corresponde a una nueva metodología (ENCOVI 2023) y no es comparable con las
canastas previas.
"""

from __future__ import annotations

import re
import unicodedata

SPANISH_MONTHS: tuple[str, ...] = (
    "Enero",
    "Febrero",
    "Marzo",
    "Abril",
    "Mayo",
    "Junio",
    "Julio",
    "Agosto",
    "Septiembre",
    "Octubre",
    "Noviembre",
    "Diciembre",
)

FIRST_COMPARABLE_YEAR = 2024
FIRST_COMPARABLE_PERIOD = "2024-01"


def _normalize(value: str) -> str:
    """Minúsculas, sin acentos, sin puntos finales y con espacios colapsados."""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.strip().lower().rstrip(".")
    return re.sub(r"\s+", " ", text)


_MONTH_LOOKUP: dict[str, int] = {
    _normalize(name): number for number, name in enumerate(SPANISH_MONTHS, start=1)
}
# Variantes observadas en fuentes públicas del INE y en exports de Excel.
_MONTH_LOOKUP.update({"setiembre": 9, "sept": 9, "sep": 9})


def month_number(value: str | int) -> int:
    """Devuelve el número de mes (1-12) a partir del nombre en español.

    >>> month_number("Septiembre")
    9
    >>> month_number("octubre")
    10
    """
    if isinstance(value, bool):  # bool es subclase de int
        raise TypeError("Se esperaba un nombre de mes o un entero, no un booleano")
    if isinstance(value, int):
        if 1 <= value <= 12:
            return value
        raise ValueError(f"Mes fuera de rango: {value!r}")
    key = _normalize(value)
    try:
        return _MONTH_LOOKUP[key]
    except KeyError as exc:
        raise ValueError(f"Mes no reconocido: {value!r}") from exc


def month_name(number: int) -> str:
    """Devuelve el nombre canónico del mes (1-12) en español."""
    if not 1 <= int(number) <= 12:
        raise ValueError(f"Mes fuera de rango: {number!r}")
    return SPANISH_MONTHS[int(number) - 1]


def month_sort_key(year: int, month: str | int) -> tuple[int, int]:
    """Clave de orden cronológica, nunca alfabética."""
    return int(year), month_number(month)


def period(year: int, month: str | int) -> str:
    """Etiqueta ISO de periodo comparable, por ejemplo ``2024-09``."""
    return f"{int(year):04d}-{month_number(month):02d}"


def parse_period(label: str) -> tuple[int, int]:
    """Convierte ``"2025-01"`` en ``(2025, 1)``."""
    match = re.fullmatch(r"(\d{4})-(\d{1,2})", str(label).strip())
    if not match:
        raise ValueError(f"Periodo inválido: {label!r}; se esperaba AAAA-MM")
    year, month = int(match.group(1)), int(match.group(2))
    if not 1 <= month <= 12:
        raise ValueError(f"Periodo inválido: {label!r}")
    return year, month


def month_index(year: int, month: str | int) -> int:
    """Índice absoluto de mes, útil para restar periodos."""
    return int(year) * 12 + (month_number(month) - 1)


def period_range(first: str, last: str) -> list[str]:
    """Lista inclusiva de periodos ``AAAA-MM`` entre dos extremos."""
    start_year, start_month = parse_period(first)
    end_year, end_month = parse_period(last)
    if (start_year, start_month) > (end_year, end_month):
        raise ValueError(f"Rango invertido: {first!r} > {last!r}")
    cursor = month_index(start_year, start_month)
    final = month_index(end_year, end_month)
    return [f"{cursor // 12:04d}-{cursor % 12 + 1:02d}" for cursor in range(cursor, final + 1)]


def shift_period(label: str, months: int) -> str:
    """Desplaza un periodo ``months`` meses (negativo para ir al pasado)."""
    year, month = parse_period(label)
    cursor = month_index(year, month) + int(months)
    return f"{cursor // 12:04d}-{cursor % 12 + 1:02d}"


def assert_comparable_period(label: str) -> None:
    """La CBA 2024-2026 rompe la metodología previa: no se acepta 2023 o antes."""
    if str(label) < FIRST_COMPARABLE_PERIOD:
        raise ValueError(
            f"El periodo {label} es anterior a {FIRST_COMPARABLE_PERIOD}. "
            "La CBA 2024-2026 usa una metodología distinta y no es comparable "
            "con canastas previas sin una nota de quiebre metodológico."
        )
