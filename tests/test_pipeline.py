from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest


pytestmark = pytest.mark.integration


def load_payload(out_dir: Path) -> dict:
    return json.loads((out_dir / "indicators.json").read_text(encoding="utf-8"))


def load_provenance(out_dir: Path) -> dict:
    return json.loads((out_dir / "provenance.json").read_text(encoding="utf-8"))


def test_all_340_municipalities_join_without_dropped_codes(built_outputs):
    _summary, out_dir = built_outputs
    payload = load_payload(out_dir)
    codes = [m["municipio_codigo"] for m in payload["municipalities"]]

    assert payload["municipality_count"] == 340
    assert payload["department_count"] == 22
    assert len(codes) == 340
    assert len(set(codes)) == 340
    assert all(len(code) == 4 and code.isdigit() for code in codes)
    assert payload["data_quality"]["municipality_count"] == 340
    assert "340 de 340" in payload["data_quality"]["join_status"]

    # Every source that claims municipal coverage must have all 340 codes.
    assert (
        payload["data_quality"]["mineduc_2022"]["establishments"]["total_schools"] > 0
    )
    assert payload["data_quality"]["vital_events_2025"]["births"]["rows_used"] > 0
    assert payload["data_quality"]["vital_events_2025"]["deaths"]["rows_used"] > 0
    assert payload["data_quality"]["segeplan"]["poverty_2023"]["rows"] == 340
    assert payload["data_quality"]["segeplan"]["allocation_2026"]["rows"] == 340


def test_guatemala_plus_21_crosswalk_is_applied_to_16_municipalities(built_outputs):
    _summary, out_dir = built_outputs
    payload = load_payload(out_dir)
    crosswalk = payload["data_quality"]["crosswalk"]

    assert crosswalk["crosswalk_applied"] == 16
    assert crosswalk["crosswalk_mapping"] == (
        "0123-0138 -> 0102-0117 (restar 21 al correlativo municipal)"
    )
    # The 16 mapped codes are present and no source code leaked into the output.
    codes = {m["municipio_codigo"] for m in payload["municipalities"]}
    assert {f"01{n:02d}" for n in range(2, 18)} <= codes
    assert not ({f"01{n:02d}" for n in range(23, 39)} & codes)
    assert (
        payload["data_quality"]["projection_overlap"]["max_abs_difference_people"] == 0
    )


def test_suppression_is_visible_and_does_not_leak_small_counts(built_outputs):
    _summary, out_dir = built_outputs
    payload = load_payload(out_dir)
    suppression = payload["suppression"]

    assert suppression["threshold"] == 5
    assert suppression["total_suppressed_cells"] > 0
    under5 = suppression["counts"]["suppressed_cells_by_field"][
        "defunciones_menores_5_2025"
    ]
    assert under5 > 0

    for municipality in payload["municipalities"]:
        fields = municipality["campos_suprimidos"]
        value = municipality["defunciones_menores_5_2025"]
        assert all(not field.endswith("_suprimido") for field in fields)
        if "defunciones_menores_5_2025" in fields:
            assert value is None
            assert municipality["tasa_mortalidad_menor_5_2025"] is None
        else:
            assert value is None or value == 0 or value >= 5
        if municipality["tiene_supresion"]:
            assert fields
        # A suppressed value must not survive under a differently named key.
        assert "defunciones_menores_5_2025_raw" not in municipality


def test_every_series_has_license_metadata_and_download_provenance(built_outputs):
    _summary, out_dir = built_outputs
    payload = load_payload(out_dir)
    sources = payload["sources"]
    source_ids = {source["id"] for source in sources}

    assert len(sources) >= 9
    for source in sources:
        assert source["license"]["id"]
        assert source["license"]["name"]
        assert source["license_status"]
        assert source["download_url"].startswith("https://")
        assert source["dataset_page"].startswith("https://")
        assert source["sha256"] and len(source["sha256"]) == 64
        assert source["downloaded_at_utc"].endswith("Z")
        assert source["attribution"]
        assert source["license_notice"]

    for definition in payload["indicators"]:
        assert definition["sources"], definition["key"]
        assert set(definition["sources"]) <= source_ids, definition["key"]
        assert definition["license_summary"]
        for metadata in definition["source_metadata"]:
            assert metadata is not None
            assert metadata["license"]["name"]


def test_segeplan_is_non_commercial_and_mineduc_is_cc0(built_outputs):
    _summary, out_dir = built_outputs
    payload = load_payload(out_dir)
    sources = {source["id"]: source for source in payload["sources"]}

    for source_id in ("segeplan-pobreza-2023", "segeplan-asignacion-2026"):
        source = sources[source_id]
        assert source["license"]["id"] == "cc-nc"
        assert source["license"]["commercial_use"] is False
        assert source["non_commercial"] is True
        assert "no comercial" in source["license_notice"].lower()
        assert (
            source["license"]["url"] == "http://creativecommons.org/licenses/by-nc/2.0/"
        )

    for source_id in ("mineduc-establecimientos-2022", "mineduc-estudiantes-2022"):
        source = sources[source_id]
        assert source["license"]["id"] == "cc-zero"
        assert source["license"]["commercial_use"] is True
        assert source["ckan_license_id"] == "cc-zero"


def test_ine_sources_have_exact_urls_and_ckan_status(built_outputs):
    _summary, out_dir = built_outputs
    payload = load_payload(out_dir)
    sources = {source["id"]: source for source in payload["sources"]}

    assert sources["ine-proyecciones-2035"]["download_url"].startswith(
        "https://www.ine.gob.gt/ine/wp-content/uploads/2020/08/"
    )
    assert sources["ine-proyecciones-2030"]["ckan_license_id"] == "odc-by"
    assert sources["ine-proyecciones-2030"]["license_status"] == "declared"
    assert sources["ine-nacimientos-2025"]["ckan_license_id"] is None
    assert sources["ine-nacimientos-2025"]["license_status"] == "not_declared"
    assert sources["ine-defunciones-2025"]["license_status"] == "not_declared"
    assert sources["ine-catalogo-municipal-340"]["download_status"] == "derived"


def test_provenance_manifest_records_outputs_and_transformations(built_outputs):
    _summary, out_dir = built_outputs
    provenance = load_provenance(out_dir)
    payload = load_payload(out_dir)

    assert provenance["snapshot_id"] == payload["snapshot_id"]
    assert provenance["generated_at_utc"].endswith("Z")
    assert provenance["transformations"]["projections_2030"]["crosswalk_applied"] == 16
    assert provenance["transformations"]["projection_overlap"]["status"] == "ok"
    assert provenance["transformations"]["births_2025"]["rows_unmatched"] > 0
    assert provenance["transformations"]["deaths_2025"]["rows_unmatched"] > 0
    assert provenance["transformations"]["indicators"]["rows"] == 340

    for output in provenance["outputs"]:
        path = Path(output)
        assert path.exists(), path
        assert len(provenance["outputs"][output]["sha256"]) == 64


def test_parquet_output_is_340_rows_and_keeps_suppression_as_null(built_outputs):
    _summary, out_dir = built_outputs
    frame = pd.read_parquet(out_dir / "indicators.parquet")
    reference = pd.read_parquet(out_dir / "municipios.parquet")

    assert len(frame) == 340
    assert len(reference) == 340
    assert frame["municipio_codigo"].nunique() == 340
    assert set(frame["municipio_codigo"]) == set(reference["municipio_codigo"])
    suppressed = frame["defunciones_menores_5_2025"].isna() & frame[
        "defunciones_menores_5_2025_suprimido"
    ].fillna(False).astype(bool)
    assert suppressed.sum() > 0
    assert frame.loc[suppressed, "tasa_mortalidad_menor_5_2025"].isna().all()
