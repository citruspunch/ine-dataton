from __future__ import annotations

import re
from pathlib import Path


def _walk_keys(value, path="$"):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, f"{path}.{key}"
            yield from _walk_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_keys(child, f"{path}[{index}]")


def test_crosswalk_has_all_340_municipalities(artifacts):
    meta = artifacts["meta"]
    payload = artifacts["municipalities"]
    profiles = artifacts["profiles"]

    assert len(payload["municipalities"]) == 340
    assert len(profiles) == 340
    assert len({item["code"] for item in payload["municipalities"]}) == 340
    assert len(payload["departments"]) == 22
    assert meta["coverage"]["crosswalk"] == "340/340"
    assert meta["coverage"]["municipalities"] == 340
    assert meta["coverage"]["departments"] == 22

    for year in ("2021", "2022", "2024"):
        assert meta["coverage"]["dinese_pairs"][year] == "340/340"

    # Every municipality must appear in every DINESE year, and the
    # municipality-level counts must rebuild the national totals exactly.
    for year in ("2021", "2022", "2024"):
        if year == "2024":
            total = sum(
                profile["snapshot_2024"]["total"] for profile in profiles.values()
            )
        else:
            total = sum(
                profile["series_2021_2022"][year]["total"]
                for profile in profiles.values()
            )
        assert total == meta["national"]["dinese"][year]["total"]

    for municipality in payload["municipalities"]:
        assert re.fullmatch(r"\d{4}", municipality["code"]), municipality["code"]
        assert municipality["department_code"] == municipality["code"][:2]
        for rank in municipality["ranks"].values():
            assert 1 <= rank <= 340


def test_2024_snapshot_is_separated_from_2021_2022_series(artifacts):
    meta = artifacts["meta"]
    profiles = artifacts["profiles"]
    manifest = artifacts["manifest"]

    views = {view["id"]: view for view in meta["views"]}
    assert set(views) == {"2024", "series"}
    assert views["2024"]["dinese_years"] == [2024]
    assert views["series"]["dinese_years"] == [2021, 2022]
    assert views["2024"]["total_establishments"] == 645_431
    assert views["series"]["total_establishments"] == {
        "2021": 312_923,
        "2022": 313_272,
    }

    assert manifest["separation"]["snapshot"]["profile_key"] == "snapshot_2024"
    assert manifest["separation"]["series"]["profile_key"] == "series_2021_2022"
    assert manifest["separation"]["snapshot"]["years"] == [2024]
    assert manifest["separation"]["series"]["years"] == [2021, 2022]

    for profile in profiles.values():
        snapshot = profile["snapshot_2024"]
        series = profile["series_2021_2022"]
        assert snapshot["year"] == 2024
        assert set(snapshot) == {"year", "total", "ciiu", "size", "legal"}
        assert set(series) == {"years", "2021", "2022"}
        assert series["years"] == [2021, 2022]
        assert series["2021"]["year"] == 2021
        assert series["2022"]["year"] == 2022
        assert "2024" not in series
        assert "2021" not in snapshot
        assert snapshot["total"] > 0


def test_places_suffix_999_and_missing_coordinates_are_not_map_points(artifacts):
    profiles = artifacts["profiles"]
    meta = artifacts["meta"]
    coverage = meta["coverage"]

    total = 0
    suffix_999 = 0
    missing = 0
    union = 0
    map_points = 0

    for profile in profiles.values():
        places = profile["places"]
        total += places["total"]
        suffix_999 += places["excluded"]["suffix_999"]
        missing += places["excluded"]["missing_coordinates"]
        union += places["excluded"]["union"]
        map_points += places["map_points"]

        computed_points = 0
        for item in places["items"]:
            assert (not item["excluded"]) or item["reasons"]
            if item["excluded"]:
                assert item["reasons"]
                if item["code"].endswith("999"):
                    assert "sufijo_999" in item["reasons"]
                if item["lon"] is None or item["lat"] is None:
                    assert "sin_coordenadas" in item["reasons"]
            else:
                assert not item["code"].endswith("999")
                assert item["lon"] is not None and item["lat"] is not None
                computed_points += 1

        assert computed_points == places["map_points"]
        assert len(places["items"]) == places["total"]

    assert total == 20_036
    assert suffix_999 == 301
    assert missing == 313
    assert union == 313
    assert map_points == 19_723

    assert coverage["places_total"] == 20_036
    assert coverage["places_excluded_suffix_999"] == 301
    assert coverage["places_excluded_missing_coordinates"] == 313
    assert coverage["places_excluded_union"] == 313
    assert coverage["places_map_points"] == 19_723

    nahuala = profiles["0705"]["places"]
    assert nahuala["total"] == 100
    assert nahuala["map_points"] == 94
    assert nahuala["excluded"] == {
        "suffix_999": 1,
        "missing_coordinates": 6,
        "union": 6,
        "both": 1,
    }


def test_dinese_metrics_are_aggregates_without_firm_ids_or_employment(artifacts):
    profiles = artifacts["profiles"]
    manifest = artifacts["manifest"]

    assert manifest["privacy"]["contains_firm_ids"] is False
    assert manifest["privacy"]["contains_employment"] is False
    assert manifest["privacy"]["contains_microdata"] is False

    forbidden = (
        "codigo_empresa",
        "firm_id",
        "empresa_id",
        "empleo",
        "employment",
        "trabajadores",
        "salarios",
    )

    for code, profile in profiles.items():
        for key, location in _walk_keys(profile):
            lowered = key.lower()
            assert not any(word in lowered for word in forbidden), location
        assert set(profile["snapshot_2024"]) == {
            "year",
            "total",
            "ciiu",
            "size",
            "legal",
        }
        assert "CÓDIGO" not in profile
        assert code == profile["code"]


def test_ciiu_size_and_legal_totals_are_consistent(artifacts):
    meta = artifacts["meta"]
    profiles = artifacts["profiles"]

    ciiu_letters = {section["letter"] for section in meta["ciiu_sections"]}
    assert len(ciiu_letters) == 21
    assert set(meta["size_order"]) == {"Micro", "Pequeña", "Mediana", "Grande"}

    for profile in profiles.values():
        for payload in (
            profile["snapshot_2024"],
            profile["series_2021_2022"]["2021"],
            profile["series_2021_2022"]["2022"],
        ):
            assert set(payload["ciiu"]) == ciiu_letters
            assert sum(payload["ciiu"].values()) == payload["total"]
            assert sum(payload["size"].values()) == payload["total"]
            assert sum(payload["legal"].values()) == payload["total"]

    for year in ("2021", "2022", "2024"):
        national = meta["national"]["dinese"][year]
        aggregated_ciiu = {letter: 0 for letter in ciiu_letters}
        for profile in profiles.values():
            payload = (
                profile["snapshot_2024"]
                if year == "2024"
                else profile["series_2021_2022"][year]
            )
            for letter, value in payload["ciiu"].items():
                aggregated_ciiu[letter] += value
        assert aggregated_ciiu == national["ciiu"]


def test_population_sums_to_census_totals(artifacts):
    meta = artifacts["meta"]
    profiles = artifacts["profiles"]

    assert meta["national"]["population"]["total"] == 14_901_286
    assert (
        sum(group["count"] for group in meta["national"]["population"]["age_groups"])
        == 14_901_286
    )

    for profile in profiles.values():
        population = profile["population"]
        assert (
            sum(group["count"] for group in population["age_groups"])
            == population["total"]
        )
        assert population["men"] + population["women"] == population["total"]
        assert population["urban"] + population["rural"] == population["total"]
        summary = population["age_summary"]
        assert (
            summary["under_15"] + summary["working_age"] + summary["over_64"]
            == population["total"]
        )


def test_legal_status_recoding_is_explicit(artifacts):
    meta = artifacts["meta"]
    profiles = artifacts["profiles"]
    notices = meta["notices"]

    assert len(meta["legal_categories"]["2021"]) == 30
    assert len(meta["legal_categories"]["2022"]) == 29
    assert len(meta["legal_categories"]["2024"]) == 15
    assert len(meta["legal_categories"]["series"]) == 30

    assert "30" in notices["2024"]["body"]
    assert "15" in notices["2024"]["body"]
    assert "312,923" in notices["2024"]["body"]
    assert "645,431" in notices["2024"]["body"]
    assert "+106.3" in notices["2024"]["body"]
    assert "313,272" in notices["series"]["body"]
    assert "+0.1" in notices["series"]["body"]

    for profile in profiles.values():
        assert len(profile["snapshot_2024"]["legal"]) == 15
        assert len(profile["series_2021_2022"]["2021"]["legal"]) == 30
        assert len(profile["series_2021_2022"]["2022"]["legal"]) == 29


def test_provenance_manifest_has_url_timestamp_and_hash_for_every_file(artifacts):
    meta = artifacts["meta"]
    manifest = artifacts["manifest"]

    assert len(meta["sources"]) == 5
    for source in meta["sources"]:
        assert source["url"].startswith("https://datos.ine.gob.gt/")
        assert source["url"].endswith(".xlsx")
        assert re.fullmatch(r"[0-9a-f]{64}", source["sha256"]), source["sha256"]
        assert source["downloaded_at_utc"].endswith("Z")
        assert source["bytes"] > 0
        assert source["license"]["status"]
        assert source["license"]["id"] == "cc-by"

    assert len(manifest["inputs"]) == 5
    for item in manifest["inputs"]:
        assert item["build_sha256"] == item["sha256"]

    out_dir: Path = artifacts["out_dir"]
    listed = {entry["path"] for entry in manifest["outputs"]}
    assert "meta.json" in listed
    assert "municipalities.json" in listed
    assert "profiles/0101.json" in listed
    assert len(listed) == 342
    assert "manifest.json" not in listed

    import hashlib

    for entry in manifest["outputs"]:
        path = out_dir / entry["path"]
        assert path.exists(), entry["path"]
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        assert digest == entry["sha256"], entry["path"]
