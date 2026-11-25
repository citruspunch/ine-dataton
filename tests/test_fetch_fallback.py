from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from radar.config import Source
from radar.fetch import SourceError, ensure_sources, sha256_file


def _write_fake_xlsx(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("xl/workbook.xml", "<workbook/>")
        archive.writestr("[Content_Types].xml", "<Types/>")


def test_missing_xlsx_triggers_official_ine_fallback(tmp_path):
    source = Source(
        "nacimientos_2025.xlsx",
        "https://datos.ine.gob.gt/dataset/demo/resource/demo/download/nacimientos_2025.xlsx",
        "xlsx",
        "Datos abiertos INE",
        "INE",
    )
    calls: list[str] = []

    def fake_downloader(url: str, destination: Path) -> None:
        calls.append(url)
        _write_fake_xlsx(destination)

    manifest_path = tmp_path / "provenance.json"
    rows = ensure_sources(
        [source],
        tmp_path,
        manifest_path,
        downloader=fake_downloader,
        now="2026-11-25T04:30:00Z",
    )
    assert calls == [source.url]
    assert (tmp_path / "nacimientos_2025.xlsx").exists()
    row = rows[0]
    assert row["status"] == "downloaded"
    assert row["url"] == source.url
    assert row["retrieved_at_utc"] == "2026-11-25T04:30:00Z"
    assert row["sha256"] == sha256_file(tmp_path / "nacimientos_2025.xlsx")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["sources"][0]["url"] == source.url


def test_local_file_wins_and_no_download_happens(tmp_path):
    source = Source(
        "demo.xlsx", "https://example.invalid/demo.xlsx", "xlsx", "test", "test"
    )
    _write_fake_xlsx(tmp_path / "demo.xlsx")
    calls: list[str] = []

    def fake_downloader(url: str, destination: Path) -> None:
        calls.append(url)

    rows = ensure_sources(
        [source], tmp_path, tmp_path / "provenance.json", downloader=fake_downloader
    )
    assert calls == []
    assert rows[0]["status"] == "cached"
    assert rows[0]["origin"] == "local-cache"


def test_corrupt_local_file_is_replaced(tmp_path):
    source = Source(
        "demo.xlsx", "https://example.invalid/demo.xlsx", "xlsx", "test", "test"
    )
    (tmp_path / "demo.xlsx").write_text("not an xlsx", encoding="utf-8")
    calls: list[str] = []

    def fake_downloader(url: str, destination: Path) -> None:
        calls.append(url)
        _write_fake_xlsx(destination)

    rows = ensure_sources(
        [source], tmp_path, tmp_path / "provenance.json", downloader=fake_downloader
    )
    assert calls == [source.url]
    assert rows[0]["status"] == "downloaded"


def test_offline_run_fails_when_file_is_missing(tmp_path):
    source = Source(
        "demo.xlsx", "https://example.invalid/demo.xlsx", "xlsx", "test", "test"
    )
    with pytest.raises(SourceError):
        ensure_sources(
            [source],
            tmp_path,
            tmp_path / "provenance.json",
            allow_network=False,
        )
