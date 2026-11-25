"""Errores explícitos del proceso de ingesta."""

from __future__ import annotations


class IngestError(RuntimeError):
    """Falla controlada cuando un archivo falta, no tiene el formato esperado
    o rompe una regla de consistencia de los datos del INE."""


class PeriodNotAvailableError(IngestError):
    """El periodo solicitado está fuera del alcance comparable (2024-2026)."""
