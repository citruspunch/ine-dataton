"""Reading of the accepted shapes: delimited CSV, XLSX and legacy XLS.

No free URLs: the path comes from the closed-list manifest and is resolved
inside the repository. The header row is declared by the profile, never
inferred.
"""

from __future__ import annotations

import csv
import datetime as dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ReadError(Exception):
    """The file cannot be read: the rule stays not evaluated, not failed."""


class UnexpectedSheet(Exception):
    """The observed sheet is not the declared one. A clear discrepancy, not an
    unreadable file."""

    def __init__(self, expected: str, observed: list[str]) -> None:
        super().__init__(f"hoja declarada {expected!r}; hojas observadas {observed!r}")
        self.expected = expected
        self.observed = observed


MONTH_NAMES = {
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
    "diciembre": 12,
}


@dataclass
class Table:
    path: Path
    sheet: str | None
    header: list[str]
    header_row: int = 1
    rows: list[dict[str, Any]] = field(default_factory=list)
    row_numbers: list[int] = field(default_factory=list)
    cells: dict[int, list[Any]] = field(default_factory=dict)

    def column_index(self, header: str) -> int | None:
        try:
            return self.header.index(header)
        except ValueError:
            return None

    def cell(self, row_number: int, index: int) -> Any:
        """Raw value by column position, independent of the header name."""
        values = self.cells.get(row_number, [])
        return values[index] if index < len(values) else None

    def letter_index(self, letter: str) -> int:
        """A -> 0, B -> 1, ... AA -> 26."""
        n = 0
        for ch in letter:
            n = n * 26 + (ord(ch.upper()) - 64)
        return n - 1

    def letter(self, index: int) -> str:
        """0 -> A, 25 -> Z, 26 -> AA. Evidence metadata only."""
        text = ""
        n = index + 1
        while n:
            n, rest = divmod(n - 1, 26)
            text = chr(65 + rest) + text
        return text

    def row_at(self, row_number: int) -> dict[str, Any] | None:
        for num, row in zip(self.row_numbers, self.rows):
            if num == row_number:
                return row
        return None


def read_table(
    path: Path,
    kind: str,
    expected_sheet: str | None = None,
    header_row: int = 1,
) -> Table:
    if not path.exists():
        raise ReadError(f"archivo no encontrado: {path.name}")
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _read_csv(path, header_row)
    if suffix == ".xls":
        return _read_xls(path, expected_sheet, header_row)
    if suffix in (".xlsx", ".xlsm"):
        return _read_xlsx(path, expected_sheet, header_row)
    if kind == "delimited":
        return _read_csv(path, header_row)
    if kind == "xlsx":
        return _read_xlsx(path, expected_sheet, header_row)
    raise ReadError(f"tipo de archivo no soportado: {kind}")


def _blank_row(values: list[Any]) -> bool:
    return all(
        value is None or (isinstance(value, str) and not value.strip())
        for value in values
    )


def _read_xls(path: Path, expected_sheet: str | None, header_row: int) -> Table:
    """Legacy .xls (BIFF) format, read with xlrd."""
    try:
        import xlrd
    except ImportError as exc:  # pragma: no cover
        raise ReadError("xlrd no instalado: no se puede abrir .xls") from exc

    try:
        book = xlrd.open_workbook(str(path))
    except Exception as exc:
        raise ReadError(f".xls ilegible: {exc}") from exc

    names = book.sheet_names()
    if not names:
        raise ReadError(".xls sin hojas")
    if expected_sheet is not None and expected_sheet not in names:
        raise UnexpectedSheet(expected_sheet, names)

    sheet_name = expected_sheet or names[0]
    sheet = book.sheet_by_name(sheet_name)
    if sheet.nrows < header_row:
        raise ReadError(f".xls sin fila de encabezado {header_row}")

    header = [str(cell.value).strip() for cell in sheet.row(header_row - 1)]
    table = Table(path=path, sheet=sheet_name, header=header, header_row=header_row)
    for index in range(header_row, sheet.nrows):
        values = sheet.row_values(index)
        if _blank_row(values):
            continue
        row_number = index + 1
        table.rows.append(dict(zip(header, values)))
        table.row_numbers.append(row_number)
        table.cells[row_number] = values
    return table


def _read_csv(path: Path, header_row: int) -> Table:
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as fh:
            raw = list(csv.reader(fh))
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        raise ReadError(f"CSV ilegible: {exc}") from exc
    if len(raw) < header_row:
        raise ReadError("CSV vacío o sin la fila de encabezado declarada")

    header = [h.strip() for h in raw[header_row - 1]]
    table = Table(path=path, sheet=None, header=header, header_row=header_row)
    for offset, values in enumerate(raw[header_row:], start=header_row + 1):
        if _blank_row(values):
            continue
        table.rows.append(dict(zip(header, values)))
        table.row_numbers.append(offset)
        table.cells[offset] = values
    return table


def _read_xlsx(path: Path, expected_sheet: str | None, header_row: int) -> Table:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:  # pragma: no cover
        raise ReadError("openpyxl no instalado") from exc

    try:
        wb = load_workbook(path, read_only=True, data_only=True)
    except Exception as exc:
        raise ReadError(f"XLSX ilegible: {exc}") from exc

    try:
        names = list(wb.sheetnames)
        if not names:
            raise ReadError("XLSX sin hojas")
        if expected_sheet is not None and expected_sheet not in names:
            raise UnexpectedSheet(expected_sheet, names)
        sheet_name = expected_sheet or names[0]
        ws = wb[sheet_name]

        header: list[str] | None = None
        table = Table(path=path, sheet=sheet_name, header=[], header_row=header_row)
        for idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if idx < header_row:
                continue
            if header is None:
                header = ["" if v is None else str(v).strip() for v in row]
                table.header = header
                continue
            if _blank_row(list(row)):
                continue
            table.rows.append(dict(zip(header, row)))
            table.row_numbers.append(idx)
            table.cells[idx] = list(row)
        if header is None:
            raise ReadError(f"XLSX sin fila de encabezado {header_row}")
        return table
    finally:
        wb.close()


def coerce(value: Any, type_name: str) -> Any:
    """Coerce a raw value to a declared type. Raises ValueError if it fails."""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError("valor vacío")

    if type_name == "string":
        return str(value).strip()

    if type_name == "float":
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        return float(str(value).strip().replace(",", "."))

    if type_name == "integer":
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            number = float(value)
        else:
            number = float(str(value).strip().replace(",", "."))
        if not number.is_integer():
            raise ValueError(f"{value!r} no es entero")
        return int(number)

    if type_name == "date":
        if isinstance(value, dt.datetime):
            return value.date().isoformat()
        if isinstance(value, dt.date):
            return value.isoformat()
        return dt.date.fromisoformat(str(value).strip()).isoformat()

    raise ValueError(f"tipo no soportado: {type_name}")


def coerce_month(value: Any, month_format: str) -> int:
    """Coerce a month cell to 1..12 using the declared convention."""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError("mes vacío")
    if month_format == "number":
        number = (
            int(float(str(value).strip())) if isinstance(value, str) else int(value)
        )
        if not 1 <= number <= 12:
            raise ValueError(f"{value!r} no es un mes entre 1 y 12")
        return number
    key = str(value).strip().lower()
    if key not in MONTH_NAMES:
        raise ValueError(f"{value!r} no es un mes en español")
    return MONTH_NAMES[key]
