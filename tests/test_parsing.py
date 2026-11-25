from __future__ import annotations

from procurement_prices.parsing import (
    normalize_text,
    parse_date,
    parse_month_es,
    parse_number,
)


def test_parse_number_with_thousands_commas_and_decimals():
    assert parse_number("1,234.56") == (1234.56, True)
    assert parse_number("4,200,000.00") == (4_200_000.0, True)
    assert parse_number("3,500.000") == (3500.0, True)
    assert parse_number("1,021.40") == (1021.4, True)
    assert parse_number("1.234,56") == (1234.56, True)
    assert parse_number("12,50") == (12.5, True)
    assert parse_number("1,234") == (1234.0, True)
    assert parse_number("0,123") == (0.123, True)
    assert parse_number("Q 1,885.87") == (1885.87, True)


def test_parse_number_rejects_placeholders_and_garbage():
    assert parse_number("Sin Dato") == (None, False)
    assert parse_number("#N/A") == (None, False)
    assert parse_number("") == (None, False)
    assert parse_number(None) == (None, False)
    assert parse_number("no disponible") == (None, False)
    assert parse_number("-") == (None, False)


def test_parse_number_plain_values_are_not_flagged_as_commas():
    assert parse_number("23.30") == (23.3, False)
    assert parse_number(171.2) == (171.2, False)
    assert parse_number("125") == (125.0, False)


def test_parse_date_marks_impossible_negative_year_invalid():
    parsed = parse_date("30/11/-0001")
    assert parsed.status == "invalid"
    assert parsed.value is None
    assert parsed.raw == "30/11/-0001"


def test_parse_date_valid_iso_and_dmy():
    assert parse_date("01/09/2016").iso == "2016-09-01"
    assert parse_date("2023-08-04").iso == "2023-08-04"
    assert parse_date("31/02/2020").status == "invalid"
    assert parse_date("").status == "missing"
    assert parse_date(None).status == "missing"


def test_month_names_and_search_normalization():
    assert parse_month_es("Septiembre") == 9
    assert parse_month_es("NOVIENBRE") == 11
    assert parse_month_es("diciembre") == 12
    assert normalize_text("PAPEL BOND TAMAÑO CARTA") == "papel bond tamano carta"
    assert normalize_text("  Río   Frío  ") == "rio frio"
