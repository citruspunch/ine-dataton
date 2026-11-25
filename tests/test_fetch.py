from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from municipal_profile.catalog import SOURCES, Source
from municipal_profile.fetch import ensure_sources

FAKE_BYTES = b"PK\x03\x04contenido xlsx de prueba"


def make_source(tmp_path: Path, key: str = "fake_2024") -> Source:
    return Source(
        key=key,
        filename=f"{key}.xlsx",
        dataset="DINESE",
        title="Recurso de prueba",
        package_id="paquete",
        resource_id="recurso",
        url=f"https://datos.ine.gob.gt/dataset/paquete/resource/recurso/download/{key}.xlsx",
        year=2024,
        kind="dinese",
        ckan_metadata_modified="2026-03-02T00:00:00",
    )


def test_missing_xlsx_is_downloaded_and_logged_with_url_timestamp_and_hash(tmp_path):
    source = make_source(tmp_path)
    raw_dir = tmp_path / "raw"
    provenance_path = tmp_path / "provenance.json"
    calls: list[str] = []

    class FakeResponse:
        def __call__(self, url: str, destination: Path) -> int:
            calls.append(url)
            destination.write_bytes(FAKE_BYTES)
            return len(FAKE_BYTES)

    provenance = ensure_sources(
        raw_dir=raw_dir,
        provenance_path=provenance_path,
        sources=(source,),
        download=FakeResponse(),
    )

    target = raw_dir / source.filename
    assert target.exists()
    assert target.read_bytes() == FAKE_BYTES
    assert calls == [source.url]

    entry = provenance["files"][0]
    assert entry["status"] == "downloaded"
    assert entry["url"] == source.url
    assert entry["downloaded_at_utc"].endswith("Z")
    assert entry["sha256"] == hashlib.sha256(FAKE_BYTES).hexdigest()
    assert entry["bytes"] == len(FAKE_BYTES)

    assert len(provenance["downloads"]) == 1
    download = provenance["downloads"][0]
    assert download["url"] == source.url
    assert download["downloaded_at_utc"] == entry["downloaded_at_utc"]
    assert download["sha256"] == entry["sha256"]

    saved = json.loads(provenance_path.read_text(encoding="utf-8"))
    assert saved["files"][0]["sha256"] == entry["sha256"]


def test_cached_file_is_offline_and_not_redownloaded(tmp_path):
    source = make_source(tmp_path)
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    (raw_dir / source.filename).write_bytes(FAKE_BYTES)
    provenance_path = tmp_path / "provenance.json"

    def must_not_run(url: str, destination: Path) -> int:
        raise AssertionError("No debería descargarse un archivo existente")

    provenance = ensure_sources(
        raw_dir=raw_dir,
        provenance_path=provenance_path,
        sources=(source,),
        download=must_not_run,
    )
    assert provenance["files"][0]["status"] == "cached"
    assert provenance["files"][0]["timestamp_source"] == "file_mtime"
    assert provenance["files"][0]["downloaded_at_utc"].endswith("Z")
    assert provenance["downloads"] == []

    # A second run reuses the recorded timestamp instead of inventing one.
    previous_timestamp = provenance["files"][0]["downloaded_at_utc"]
    provenance_again = ensure_sources(
        raw_dir=raw_dir,
        provenance_path=provenance_path,
        sources=(source,),
        download=must_not_run,
    )
    assert provenance_again["files"][0]["downloaded_at_utc"] == previous_timestamp
    assert provenance_again["files"][0]["status"] == "cached"


def test_force_redownloads_and_appends_to_history(tmp_path):
    source = make_source(tmp_path)
    raw_dir = tmp_path / "raw"
    provenance_path = tmp_path / "provenance.json"
    calls = 0

    def fake_download(url: str, destination: Path) -> int:
        nonlocal calls
        calls += 1
        destination.write_bytes(FAKE_BYTES + str(calls).encode())
        return len(FAKE_BYTES) + 1

    ensure_sources(
        raw_dir=raw_dir,
        provenance_path=provenance_path,
        sources=(source,),
        download=fake_download,
    )
    provenance = ensure_sources(
        raw_dir=raw_dir,
        provenance_path=provenance_path,
        sources=(source,),
        download=fake_download,
        force=True,
    )
    assert calls == 2
    assert len(provenance["downloads"]) == 2
    assert provenance["files"][0]["sha256"] != provenance["downloads"][0]["sha256"]


def test_non_xlsx_payload_is_rejected_and_removed(tmp_path):
    source = make_source(tmp_path)
    raw_dir = tmp_path / "raw"
    provenance_path = tmp_path / "provenance.json"

    def html_download(url: str, destination: Path) -> int:
        destination.write_bytes(b"<html>error</html>")
        return len(b"<html>error</html>")

    with pytest.raises(RuntimeError, match="XLSX"):
        ensure_sources(
            raw_dir=raw_dir,
            provenance_path=provenance_path,
            sources=(source,),
            download=html_download,
        )
    assert not (raw_dir / source.filename).exists()
    assert not (raw_dir / f".{source.filename}.part").exists()


def test_catalogue_points_to_official_ine_urls():
    assert len(SOURCES) == 5
    for source in SOURCES:
        assert source.url.startswith("https://datos.ine.gob.gt/dataset/")
        assert source.url.endswith(".xlsx")
        assert source.page_url.startswith("https://datos.ine.gob.gt/dataset/")
        assert source.license_id == "cc-by"
