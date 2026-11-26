from pathlib import Path

from engine.reader import Table
from engine.rules import build_variables_summary, declared_periods, parse_table
from engine.profiles import _validate_schema, _validate_dates


def test_summary_distinguishes_blank_invalid_and_absent_columns():
    table = Table(
        path=Path("data.csv"),
        sheet=None,
        header=["Población"],
        row_numbers=[2, 3, 4],
        cells={2: ["10"], 3: [""], 4: ["inválido"]},
    )
    profile = {
        "schema": [
            {
                "name": "population",
                "column": "Población",
                "type": "integer",
                "unit": "personas",
                "reference": "municipio",
                "nullable": True,
            },
            {"name": "births", "column": "Nacimientos", "type": "integer"},
        ],
        "dates": {},
    }
    summary = build_variables_summary(parse_table(table, profile), profile)
    population, births = summary["columns"]
    assert (
        population["valid_count"],
        population["null_count"],
        population["excluded_count"],
    ) == (1, 1, 1)
    assert population["unit"] == "personas"
    assert population["reference"] == "municipio"
    assert births["present"] is False
    assert births["valid_count"] is None


def test_summary_supports_year_only_datasets():
    table = Table(
        path=Path("data.csv"),
        sheet=None,
        header=["Año", "Población"],
        row_numbers=[2, 3],
        cells={2: ["2024", "100"], 3: ["2025", "110"]},
    )
    profile = {
        "schema": [
            {"name": "year", "column": "Año", "type": "integer"},
            {
                "name": "population",
                "column": "Población",
                "type": "integer",
                "unit": "personas",
                "reference": "municipio",
            },
        ],
        "dates": {"year": "year", "expected": ["2024", "2025"]},
        "display": {"period": "2024 a 2025"},
        "summary_notes": "Proyección municipal.",
    }
    summary = build_variables_summary(parse_table(table, profile), profile)
    assert summary["row_count"] == 2
    assert summary["coverage"] == {
        "period": "2024 a 2025",
        "notes": "Proyección municipal.",
    }
    assert summary["columns"][1]["valid_count"] == 2


def test_annual_range_expands_by_year_and_monthly_range_by_month():
    assert declared_periods(
        {"dates": {"year": "year", "range": {"from": "2023", "to": "2025"}}}
    ) == ["2023", "2024", "2025"]
    assert declared_periods(
        {
            "dates": {
                "year": "year",
                "month": "month",
                "range": {"from": "2024-11", "to": "2025-01"},
            }
        }
    ) == ["2024-11", "2024-12", "2025-01"]


def test_column_metadata_is_type_checked():
    errors = _validate_schema(
        {
            "types": ["integer"],
            "schema": [
                {
                    "name": "x",
                    "column": "X",
                    "type": "integer",
                    "unit": 12,
                    "nullable": "false",
                }
            ],
        }
    )
    assert {error["field"] for error in errors} == {
        "schema[0].unit",
        "schema[0].nullable",
    }


def test_dates_allow_year_only_and_month_format_is_optional():
    assert (
        _validate_dates(
            {
                "schema": [
                    {"name": "year", "column": "Año", "type": "integer"},
                ],
                "dates": {"year": "year", "expected": ["2024", "2025"]},
            }
        )
        == []
    )
    assert (
        _validate_dates(
            {
                "schema": [
                    {"name": "year", "column": "Año", "type": "integer"},
                ],
                "dates": {"year": "year", "expected": ["2024-01"]},
            }
        )[0]["field"]
        == "dates.expected[0]"
    )
