from __future__ import annotations

from procurement_prices.aggregate import (
    build_catalog,
    build_summary,
    mark_duplicates,
    quality_summary,
)
from procurement_prices.baskets import load_baskets
from procurement_prices.config import RAW_DIR, SOURCES
from procurement_prices.dpir import load_dpir
from procurement_prices.icc import load_icc
from procurement_prices.ipmc import load_ipmc


def _records():
    specs = list(SOURCES.values())
    records = []
    records.extend(
        load_dpir(
            [spec for spec in specs if spec.group == "DPIR" and not spec.dictionary],
            RAW_DIR,
        )
    )
    for spec in specs:
        if spec.group == "IPMC" and not spec.dictionary:
            records.extend(load_ipmc(spec, RAW_DIR))
        if spec.group == "ICC" and not spec.dictionary:
            records.extend(load_icc(spec, RAW_DIR))
    records.extend(load_baskets([spec for spec in specs if spec.group == "BASKETS"], RAW_DIR))
    return mark_duplicates(records)


def test_real_files_build_expected_cutoffs_and_counts():
    records = _records()
    summary = build_summary(records)
    dpir = summary["groups"]["DPIR"]
    ipmc = summary["groups"]["IPMC"]
    icc = summary["groups"]["ICC"]
    baskets = summary["groups"]["BASKETS"]

    assert dpir["cutoff"] == "2023-08-04"
    assert dpir["status"] == "frozen"
    assert dpir["recordCount"] > 9_000
    assert dpir["quality"]["duplicates"] > 4_000
    assert dpir["quality"]["thousandsComma"] > 500

    assert ipmc["cutoff"] == "2026-10-01"
    assert ipmc["metrics"][0]["count"] == 8_366
    assert ipmc["metrics"][0]["unit"].startswith("Índice")

    assert icc["cutoff"] == "2026-10-01"
    assert icc["metrics"][0]["count"] == 360
    assert icc["status"] == "limited"

    assert baskets["cutoff"] == "2026-10-01"
    assert baskets["recordCount"] > 5_000
    assert any(metric["metric"] == "Costo mensual per cápita" for metric in baskets["metrics"])


def test_records_are_aggregated_and_never_carry_entity_names():
    records = _records()
    assert len(records) > 20_000
    for item in records:
        public = item.to_public()
        assert "Entidad" not in public
        assert "entidad" not in public
        assert public["sourceGroup"] in {"DPIR", "IPMC", "ICC", "BASKETS"}
        if public["value"] is not None:
            assert isinstance(public["value"], float)
        if public["date"] is not None:
            assert len(public["date"]) == 10


def test_catalog_and_quality_summaries_are_consistent():
    records = _records()
    catalog = build_catalog(records)
    quality = quality_summary(records)
    assert catalog["DPIR"]["items"]
    assert all(entry["count"] > 0 for entry in catalog["DPIR"]["items"])
    assert quality["canonicalRecords"] > 18_000
    assert quality["duplicates"] > 4_000
    assert quality["thousandsComma"] > 500
