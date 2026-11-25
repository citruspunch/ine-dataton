"""Prueba de extremo a extremo del pipeline, sin red y en un directorio temporal."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

from ine_basket.build import build_pipeline
from ine_basket.export import write_outputs

REQUIRED_FILES = (
    "costo-cba-percapita_u.xlsx",
    "costo-cba-percapita_r.xlsx",
    "historico-cbau_es_2024-2026.xlsx",
    "historico-cbar_es_2024-2026.xlsx",
    "ipc_2024_datosabiertos.xls",
    "base-de-datos-ipc-ano-2025_es.xls",
    "ipc_emprepu_es25.xlsx",
)


@pytest.fixture()
def workspace(tmp_path: Path, raw_dir: Path) -> Path:
    raw = tmp_path / "raw"
    raw.mkdir()
    for name in REQUIRED_FILES:
        shutil.copy2(raw_dir / name, raw / name)
    return tmp_path


def test_pipeline_runs_offline_and_emits_consistent_artifacts(workspace: Path) -> None:
    raw = workspace / "raw"
    processed = workspace / "processed"
    web = workspace / "web"

    result = build_pipeline(
        repo_root=workspace,
        raw_dir=raw,
        offline=True,
        clock=lambda: "2026-11-24T12:00:00Z",
    )
    exported = write_outputs(result, processed_dir=processed, web_data_dir=web)

    # Parquet legibles y con las filas esperadas.
    monthly = pd.read_parquet(processed / "cba_monthly.parquet")
    products = pd.read_parquet(processed / "cba_products.parquet")
    groups = pd.read_parquet(processed / "cba_groups.parquet")
    ipc = pd.read_parquet(processed / "ipc_monthly.parquet")
    assert len(monthly) == 68
    assert len(products) == 2244 + 2040
    assert len(groups) == 34 * 13 * 2
    assert len(ipc) == 34
    assert monthly["cost_per_1000_kcal"].notna().all()

    manifest = exported["manifest"]
    assert manifest["periods"]["count"] == 34
    assert len(manifest["sources"]) == 7
    for source in manifest["sources"]:
        assert source["source_url"].startswith("https://datos.ine.gob.gt/")
        assert len(source["sha256"]) == 64
        assert source["retrieved_from"] == "local-file"
        assert source["license"]["status"] in {"declarada", "no declarada"}

    payload = json.loads((web / "basket.json").read_text(encoding="utf-8"))
    assert payload["meta"]["period"]["first"] == "2024-01"
    assert payload["meta"]["period"]["last"] == "2026-10"
    assert payload["meta"]["splice"]["officialJan2025Monthly"] == pytest.approx(0.5015)
    assert payload["meta"]["splice"]["directJan2025Monthly"] == pytest.approx(-0.6738)

    urban = payload["areas"]["Urbana"]
    assert len(urban["months"]) == 34
    assert len(urban["products"]) == 66
    assert len(urban["groups"]) == 13
    catalog = [item["name"] for item in urban["products"]]
    assert [item["name"] for item in urban["products"] if item["zeroKcal"]] == [
        "Agua purificada",
        "Sal",
    ]
    for month in urban["months"]:
        assert len(month["productValues"]) == len(catalog)
        assert len(month["groupValues"]) == 13
        assert month["dailyKcalPerPerson"] == pytest.approx(2052.0)
    january = urban["months"][0]
    assert january["costPerThousandKcal"] == pytest.approx(12.40, abs=0.01)
    assert january["excludedCostPerPersonDay"] == pytest.approx(2.7711, abs=0.001)
    assert january["monthlyCostPerPerson"] == pytest.approx(846.30, abs=0.01)

    rural = payload["areas"]["Rural"]
    assert len(rural["products"]) == 60
    assert rural["months"][0]["dailyKcalPerPerson"] == pytest.approx(2172.0)

    ipc_rows = {row["period"]: row for row in payload["ipc"]}
    assert ipc_rows["2025-01"]["crossBaseMonthly"] is True
    assert ipc_rows["2025-01"]["officialMonthly"] == pytest.approx(0.5015)


def test_pipeline_never_sorts_months_alphabetically(workspace: Path) -> None:
    raw = workspace / "raw"
    result = build_pipeline(
        repo_root=workspace,
        raw_dir=raw,
        offline=True,
        clock=lambda: "2026-11-24T12:00:00Z",
    )
    periods = (
        result.tables["cba_monthly"].loc[lambda frame: frame["area"] == "Urbana", "period"].tolist()
    )
    assert periods == sorted(periods)
    sept = periods.index("2024-09")
    oct_ = periods.index("2024-10")
    assert sept < oct_
