"""Generación determinista de los fixtures sintéticos.

Cada fixture es sintético, está rotulado como tal en el manifiesto y demuestra
un caso concreto. Ninguno contiene microdatos, PII ni datos oficiales.
"""

from __future__ import annotations

import csv
import datetime as dt
import shutil
from pathlib import Path

CONTRATO_ROWS = [
    (2025, 1, "serie_mensual_sintetica", "100.00", "indice"),
    (2025, 2, "serie_mensual_sintetica", "100.42", "indice"),
    (2025, 3, "serie_mensual_sintetica", "100.91", "indice"),
]

CONTRATO_HEADER = ["anio", "mes", "indicador", "valor", "unidad"]

IDENTIDAD_ROWS = [
    (2024, 1, "1200", "registro"),
    (2024, 2, "1180", "registro"),
    (2024, 3, "1245", "registro"),
]

IDENTIDAD_HEADER = ["anio", "mes", "eventos", "unidad"]

FIXED_CREATED = dt.datetime(2026, 11, 23, 12, 0, 0)


def _write_csv(path: Path, header: list[str], rows: list[tuple]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def _normalize_zip(path: Path) -> None:
    """Reescribe el XLSX para que los bytes sean reproducibles.

    openpyxl sella el reloj en cada entrada del ZIP y vuelve a escribir la fecha
    de modificación en docProps/core.xml al guardar. Aquí se fijan ambos.
    """
    import io
    import re
    import zipfile

    with zipfile.ZipFile(path) as src:
        entries = [(info, src.read(info.filename)) for info in src.infolist()]

    fixed = b'<dcterms:modified xsi:type="dcterms:W3CDTF">2026-11-23T12:00:00Z</dcterms:modified>'
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as dst:
        for info, data in entries:
            if info.filename == "docProps/core.xml":
                data = re.sub(
                    rb"<dcterms:modified[^>]*>[^<]*</dcterms:modified>", fixed, data
                )
            entry = zipfile.ZipInfo(info.filename, date_time=(1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = info.external_attr
            dst.writestr(entry, data)
    path.write_bytes(buffer.getvalue())


def _write_xlsx(path: Path, sheet: str, header: list[str], rows: list[tuple]) -> None:
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws.title = sheet
    ws.append(header)
    for row in rows:
        ws.append([_xlsx_value(v) for v in row])
    wb.properties.creator = "INE Data Trust (fixture sintético)"
    wb.properties.created = FIXED_CREATED
    wb.properties.modified = FIXED_CREATED
    wb.properties.lastModifiedBy = "INE Data Trust"
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)
    _normalize_zip(path)


def _xlsx_value(value):
    text = str(value)
    try:
        if "." in text:
            return float(text)
        return int(text)
    except ValueError:
        return value


def write_fixtures(directory: Path) -> list[str]:
    """Escribe todos los fixtures y devuelve sus nombres."""
    directory.mkdir(parents=True, exist_ok=True)

    _write_csv(directory / "contrato_ok.csv", CONTRATO_HEADER, CONTRATO_ROWS)

    _write_csv(
        directory / "contrato_columna_faltante.csv",
        ["anio", "mes", "indicador", "valor"],
        [row[:4] for row in CONTRATO_ROWS],
    )

    duplicado = CONTRATO_ROWS + [
        (2025, 2, "serie_mensual_sintetica", "100.42", "indice")
    ]
    _write_csv(directory / "contrato_grano_duplicado.csv", CONTRATO_HEADER, duplicado)

    _write_xlsx(directory / "contrato_ok.xlsx", "Datos", CONTRATO_HEADER, CONTRATO_ROWS)
    _write_xlsx(
        directory / "contrato_hoja_inesperada.xlsx",
        "Resumen",
        CONTRATO_HEADER,
        CONTRATO_ROWS,
    )

    # Mismos bytes, dos etiquetas: la copia es deliberadamente byte a byte.
    origen = directory / "identidad_a.csv"
    _write_csv(origen, IDENTIDAD_HEADER, IDENTIDAD_ROWS)
    shutil.copyfile(origen, directory / "identidad_b.csv")

    return sorted(p.name for p in directory.iterdir() if p.is_file())
