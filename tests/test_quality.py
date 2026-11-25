from __future__ import annotations

from procurement_prices.aggregate import (
    build_group_summary,
    mark_duplicates,
    metric_stats,
    quality_summary,
)
from procurement_prices.model import Record


def record(
    *,
    rid: str,
    dataset: str,
    value: float | None,
    date: str | None = "2023-08-04",
    item: str = "Cemento gris",
    unit: str = "Saco 42.5 kg",
    nog: str = "123",
    flags: list[str] | None = None,
) -> Record:
    return Record(
        id=rid,
        source="DPIR",
        source_group="DPIR",
        dataset=dataset,
        item=item,
        category="CEMENTO",
        metric="Precio de referencia",
        value_kind="price",
        value=value,
        unit=unit,
        currency="GTQ",
        date=date,
        date_raw=date,
        date_status="valid" if date else "invalid",
        year=2023 if date else None,
        month=8 if date else None,
        nog=nog,
        status="frozen",
        flags=flags or [],
    )


def test_duplicate_prefers_the_newer_dpir_workbook():
    old = record(rid="dpir-2022-1", dataset="dpir-2022", value=100.0)
    new = record(rid="dpir-2023-1", dataset="dpir-2023", value=100.0)
    result = mark_duplicates([old, new])
    by_id = {item.id: item for item in result}
    assert "duplicate" not in by_id["dpir-2023-1"].flags
    assert "duplicate" in by_id["dpir-2022-1"].flags
    assert by_id["dpir-2022-1"].duplicate_of == "dpir-2023-1"


def test_missing_nog_copy_is_matched_to_the_complete_record():
    complete = record(rid="dpir-2022-1", dataset="dpir-2022", value=100.0, nog="6198910")
    incomplete = record(rid="dpir-2023-1", dataset="dpir-2023", value=100.0, nog="")
    result = mark_duplicates([incomplete, complete])
    by_id = {item.id: item for item in result}
    assert "duplicate" not in by_id["dpir-2022-1"].flags
    assert by_id["dpir-2023-1"].duplicate_of == "dpir-2022-1"


def test_two_different_nogs_are_not_collapsed():
    first = record(rid="a", dataset="dpir-2023", value=100.0, nog="111")
    second = record(rid="b", dataset="dpir-2023", value=100.0, nog="222")
    result = mark_duplicates([first, second])
    assert all("duplicate" not in item.flags for item in result)


def test_duplicates_within_a_file_keep_the_first_record_canonical():
    first = record(rid="dpir-2023-1", dataset="dpir-2023", value=100.0)
    second = record(rid="dpir-2023-2", dataset="dpir-2023", value=100.0)
    result = mark_duplicates([first, second])
    by_id = {item.id: item for item in result}
    assert "duplicate" not in by_id["dpir-2023-1"].flags
    assert by_id["dpir-2023-2"].duplicate_of == "dpir-2023-1"


def test_stats_exclude_duplicates_and_invalid_dates():
    items = [
        record(rid="a", dataset="dpir-2023", value=10.0, date="2023-08-01"),
        record(rid="b", dataset="dpir-2023", value=20.0, date="2023-08-02"),
        record(
            rid="c",
            dataset="dpir-2023",
            value=999.0,
            date=None,
            flags=["invalid_date"],
        ),
        record(rid="d", dataset="dpir-2023", value=30.0, date="2023-08-03"),
    ]
    stats = metric_stats(items)[0]
    assert stats["count"] == 3
    assert stats["min"] == 10.0
    assert stats["median"] == 20.0
    assert stats["max"] == 30.0
    quality = quality_summary(items)
    assert quality["invalidDate"] == 1
    assert quality["excludedFromStats"] == 1


def test_median_and_percentiles_are_correct():
    items = [
        record(rid=f"r{index}", dataset="dpir-2023", value=float(value))
        for index, value in enumerate([10, 20, 30, 40, 100])
    ]
    stats = metric_stats(items)[0]
    assert stats["min"] == 10
    assert stats["p25"] == 20
    assert stats["median"] == 30
    assert stats["p75"] == 40
    assert stats["max"] == 100


def test_comma_formatted_prices_do_not_break_summaries():
    items = [
        record(
            rid="a",
            dataset="dpir-2023",
            value=1234.56,
            flags=["thousands_comma"],
        ),
        record(rid="b", dataset="dpir-2023", value=2000.0, flags=["thousands_comma"]),
        record(rid="c", dataset="dpir-2023", value=1500.0),
    ]
    stats = metric_stats(items)[0]
    assert stats["count"] == 3
    assert stats["min"] == 1234.56
    assert stats["median"] == 1500.0
    assert stats["max"] == 2000.0
    assert quality_summary(items)["thousandsComma"] == 2


def test_group_summary_reports_frozen_cutoff_and_quality():
    items = [
        record(rid="a", dataset="dpir-2022", value=10.0, date="2022-06-01"),
        record(rid="b", dataset="dpir-2023", value=12.0, date="2023-08-04"),
        record(
            rid="c",
            dataset="dpir-2023",
            value=None,
            date="2023-08-04",
            flags=["missing_value"],
        ),
    ]
    summary = build_group_summary("DPIR", items)
    assert summary["cutoff"] == "2023-08-04"
    assert summary["status"] == "frozen"
    assert summary["quality"]["missingValue"] == 1
    assert summary["metrics"][0]["median"] == 11.0
