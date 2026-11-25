"""Territorial road-safety and health radar for Guatemala.

The package implements the local-first data pipeline described in ``PRD.md``:
it caches the official INE spreadsheets, normalises territorial codes, applies
the +21 crosswalk for the Guatemala department, suppresses small cells and
writes the JSON bundles consumed by the Next.js application.
"""

__version__ = "0.1.0"
