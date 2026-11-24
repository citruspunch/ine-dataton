"""Reading of the three accepted shapes: delimited CSV, XLSX and legacy XLS.

No free URLs: the path comes from the closed-list manifest and is resolved
inside the repository.
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


def read_table(path: Path, kind: str, expected_sheet: str | None = None) -> Table:
    if not path.exists():
        raise ReadError(f"archivo no encontrado: {path.name}")
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _read_csv(path)
    if suffix == ".xls":
        return _read_xls(path, expected_sheet)
    if suffix in (".xlsx", ".xlsm"):
        return _read_xlsx(path, expected_sheet)
    if kind == "delimited":
        return _read_csv(path)
    if kind == "xlsx":
        return _read_xlsx(path, expected_sheet)
    raise ReadError(f"tipo de archivo no soportado: {kind}")


def _read_xls(path: Path, expected_sheet: str | None) -> Table:
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
    if sheet.nrows == 0:
        raise ReadError(".xls sin fila de encabezado")

    header = [str(cell.value).strip() for cell in sheet.row(0)]
    table = Table(path=path, sheet=sheet_name, header=header)
    for index in range(1, sheet.nrows):
        values = sheet.row_values(index)
        if all(value in (None, "") for value in values):
            continue
        row_number = index + 1
        table.rows.append(dict(zip(header, values)))
        table.row_numbers.append(row_number)
        table.cells[row_number] = values
    return table


def _read_csv(path: Path) -> Table:
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.reader(fh)
            raw = list(reader)
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        raise ReadError(f"CSV ilegible: {exc}") from exc
    if not raw:
        raise ReadError("CSV vacío")
    header = [h.strip() for h in raw[0]]
    table = Table(path=path, sheet=None, header=header)
    for offset, values in enumerate(raw[1:], start=2):
        if not any(v.strip() for v in values):
            continue
        table.rows.append(dict(zip(header, values)))
        table.row_numbers.append(offset)
        table.cells[offset] = values
    return table


def _read_xlsx(path: Path, expected_sheet: str | None) -> Table:
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
        table = Table(path=path, sheet=sheet_name, header=[])
        for idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            if header is None:
                header = ["" if v is None else str(v).strip() for v in row]
                table.header = header
                continue
            if all(v is None or (isinstance(v, str) and not v.strip()) for v in row):
                continue
            table.rows.append(dict(zip(header, row)))
            table.row_numbers.append(idx)
            table.cells[idx] = list(row)
        if header is None:
            raise ReadError("XLSX sin fila de encabezado")
        return table
    finally:
        wb.close()


def coerce(value: Any, type_name: str) -> Any:
    """Coerce a raw value to the declared type. Raises ValueError if it does not
    parse."""
    if value is None:
        raise ValueError("valor vacío")
    if isinstance(value, str):
        text = value.strip()
        if text == "":
            raise ValueError("valor vacío")
    else:
        text = None

    if type_name == "string":
        return str(value).strip()

    if type_name == "number":
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        return float(str(text).replace(",", "."))

    if type_name == "integer":
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            number = float(value)
        else:
            number = float(str(text).replace(",", "."))
        if not number.is_integer():
            raise ValueError(f"{value!r} no es entero")
        return int(number)

    if type_name == "month_name":
        key = str(value).strip().lower()
        if key not in MONTH_NAMES:
            raise ValueError(f"{value!r} no es un mes en español")
        return MONTH_NAMES[key]

    if type_name == "date":
        if isinstance(value, dt.datetime):
            return value.date().isoformat()
        if isinstance(value, dt.date):
            return value.isoformat()
        return dt.date.fromisoformat(str(text)).isoformat()

    raise ValueError(f"tipo no soportado: {type_name}")
