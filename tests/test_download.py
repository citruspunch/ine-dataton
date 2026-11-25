from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from pipeline.download import (
    DownloadError,
    FetchResult,
    ensure_source,
    load_manifest,
    sha256_bytes,
)
from pipeline.sources import SOURCE_BY_ID, License, Source


TEST_LICENSE = License(
    id="test",
    name="Test license",
    url="https://example.test/license",
    commercial_use=True,
    attribution_required=True,
    ckan_license_id="test",
    ckan_license_title="Test",
    status="declared",
    notes="Fixture only.",
)


def make_source(filename: str = "test.xlsx", fmt: str = "xlsx") -> Source:
    return Source(
        id="test-source",
        title="Test source",
        publisher="Test publisher",
        dataset_page="https://example.test/dataset",
        download_url="https://example.test/download/test.xlsx",
        filename=filename,
        format=fmt,
        license=TEST_LICENSE,
        attribution="Test",
        description="Fixture source.",
        min_bytes=4,
        expected_magic=b"PK" if fmt == "xlsx" else None,
    )


def make_xlsx_bytes(padding: int = 0) -> bytes:
    """A minimal ZIP that passes the pipeline's XLSX signature check."""

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        if padding:
            archive.writestr("padding.bin", b"0" * padding)
    return buffer.getvalue()


def test_missing_xlsx_is_downloaded_and_manifested(tmp_path: Path):
    source = make_source()
    called: list[str] = []
    body = make_xlsx_bytes()

    def fake_fetcher(url: str) -> FetchResult:
        called.append(url)
        return FetchResult(
            body=body,
            http_status=200,
            content_type="application/vnd.ms-excel",
        )

    record = ensure_source(
        source,
        tmp_path,
        fetcher=fake_fetcher,
        now=datetime(2026, 11, 24, 12, 30, tzinfo=timezone.utc),
    )

    path = tmp_path / source.filename
    assert path.exists()
    assert path.read_bytes().startswith(b"PK")
    assert called == [source.download_url]
    assert record["source_id"] == source.id
    assert record["url"] == source.download_url
    assert record["downloaded_at_utc"] == "2026-11-24T12:30:00Z"
    assert record["download_status"] == "downloaded"
    assert record["sha256"] == sha256_bytes(path.read_bytes())
    assert record["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert record["bytes"] == path.stat().st_size


def test_existing_file_is_not_downloaded_again(tmp_path: Path):
    source = make_source()
    path = tmp_path / source.filename
    path.write_bytes(make_xlsx_bytes())

    def failing_fetcher(url: str) -> bytes:
        raise AssertionError("No debe descargarse un archivo que ya existe")

    first = ensure_source(source, tmp_path, fetcher=failing_fetcher)
    second = ensure_source(source, tmp_path, first, fetcher=failing_fetcher)

    assert first["download_status"] == "local_cache"
    assert second["download_status"] == "cached"
    assert second["downloaded_at_utc"] == first["downloaded_at_utc"]
    assert second["sha256"] == first["sha256"]


def test_html_error_page_is_rejected(tmp_path: Path):
    source = make_source(filename="test.csv", fmt="csv")

    def html_fetcher(url: str) -> bytes:
        return b"<!DOCTYPE html><html><body>not a csv</body></html>" + b" " * 20

    with pytest.raises(DownloadError):
        ensure_source(source, tmp_path, fetcher=html_fetcher)
    assert not (tmp_path / source.filename).exists()


def test_csv_missing_file_is_downloaded(tmp_path: Path):
    source = make_source(filename="test.csv", fmt="csv")
    body = "Codigo;Municipio\n0101;Guatemala\n".encode("utf-8")

    record = ensure_source(source, tmp_path, fetcher=lambda url: body)
    assert (tmp_path / "test.csv").read_bytes() == body
    assert record["download_status"] == "downloaded"
    assert record["content_type"] == "application/octet-stream"


def test_manifest_round_trip_is_json_serialisable(tmp_path: Path):
    source = make_source()
    record = ensure_source(source, tmp_path, fetcher=lambda url: make_xlsx_bytes())
    manifest = {"files": {source.id: record}}
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    loaded = load_manifest(tmp_path)
    assert loaded["files"][source.id]["sha256"] == record["sha256"]


def test_missing_official_ine_xlsx_is_fetched_from_the_ine_bank(tmp_path: Path):
    """The acceptance path for a missing INE .xlsx, with the real URL and time."""

    source = SOURCE_BY_ID["ine-defunciones-2025"]
    body = make_xlsx_bytes(padding=source.min_bytes)

    record = ensure_source(
        source,
        tmp_path,
        fetcher=lambda url: body,
        now=datetime(2026, 11, 24, 18, 0, tzinfo=timezone.utc),
    )

    assert record["source_id"] == "ine-defunciones-2025"
    assert record["url"] == source.download_url
    assert record["url"].startswith("https://datos.ine.gob.gt/")
    assert record["downloaded_at_utc"] == "2026-11-24T18:00:00Z"
    assert record["download_status"] == "downloaded"
    assert record["sha256"] == sha256_bytes(body)
    assert (tmp_path / source.filename).exists()


def test_local_file_with_publisher_name_is_reused_without_download(tmp_path: Path):
    """data/nacimientos_2025.xlsx should satisfy the cache without a download."""

    source = SOURCE_BY_ID["ine-nacimientos-2025"]
    original = tmp_path / "nacimientos_2025.xlsx"
    original.write_bytes(make_xlsx_bytes(padding=source.min_bytes))

    record = ensure_source(
        source,
        tmp_path,
        fetcher=lambda url: (_ for _ in ()).throw(AssertionError("No debe descargar")),
    )

    assert (tmp_path / source.filename).exists()
    assert record["download_status"] == "local_cache"
    assert record["url"] == source.download_url
    assert record["sha256"] == sha256_bytes((tmp_path / source.filename).read_bytes())
