"""Regla local-primero: si falta el archivo, se descarga y se registra procedencia."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from ine_basket.download import DatasetFile, ensure_datasets
from ine_basket.errors import IngestError
from ine_basket.registry import DatasetSpec

XLSX_PAYLOAD = b"PK\x03\x04" + b"contenido-de-prueba" * 200


def _spec(filename: str = "costo-cba-percapita_u.xlsx") -> DatasetSpec:
    return DatasetSpec(
        key="prueba",
        filename=filename,
        url="https://datos.ine.gob.gt/dataset/demo/resource/demo/download/demo.xlsx",
        title="Archivo de prueba",
        role="cba-costos",
        coverage="Prueba",
        package_id="00000000-0000-0000-0000-000000000000",
        package_name="demo",
        package_title="Demo",
        resource_id="11111111-1111-1111-1111-111111111111",
        license_id="cc-by",
        license_title="Creative Commons Attribution",
        license_url="http://www.opendefinition.org/licenses/cc-by",
        resource_last_modified_utc="2026-11-09T00:00:00Z",
    )


def test_missing_file_is_downloaded_and_recorded(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    registry = raw / "download-registry.json"
    calls: list[str] = []

    def fake_downloader(url: str, timeout: int = 120) -> bytes:
        calls.append(url)
        return XLSX_PAYLOAD

    times = iter(["2026-11-24T04:00:00Z"])
    files = ensure_datasets(
        [_spec()],
        raw,
        registry,
        downloader=fake_downloader,
        clock=lambda: next(times),
    )

    entry = files[0]
    assert calls == [_spec().url]
    assert entry.retrieved_from == "download"
    assert entry.downloaded_at_utc == "2026-11-24T04:00:00Z"
    assert entry.path.read_bytes() == XLSX_PAYLOAD
    assert entry.size_bytes == len(XLSX_PAYLOAD)
    assert entry.sha256 == hashlib.sha256(XLSX_PAYLOAD).hexdigest()

    manifest = entry.manifest_entry(tmp_path)
    assert manifest["source_url"] == _spec().url
    assert manifest["downloaded_at_utc"] == "2026-11-24T04:00:00Z"
    assert manifest["sha256"] == entry.sha256
    assert manifest["license"]["status"] == "declarada"
    assert manifest["ckan"]["package_id"] == _spec().package_id
    assert registry.exists()


def test_existing_file_is_used_without_network(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    registry = raw / "download-registry.json"

    ensure_datasets(
        [_spec()],
        raw,
        registry,
        downloader=lambda url, timeout=120: XLSX_PAYLOAD,
        clock=lambda: "2026-11-24T04:00:00Z",
    )

    def exploding_downloader(url: str, timeout: int = 120) -> bytes:  # pragma: no cover
        raise AssertionError("no debe llamarse a la red si el archivo existe")

    files = ensure_datasets(
        [_spec()],
        raw,
        registry,
        downloader=exploding_downloader,
        clock=lambda: "2026-11-25T09:30:00Z",
    )
    entry = files[0]
    assert entry.retrieved_from == "local-cache"
    assert entry.downloaded_at_utc == "2026-11-24T04:00:00Z"
    assert entry.verified_at_utc == "2026-11-25T09:30:00Z"


def test_refresh_forces_a_new_download(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    registry = raw / "download-registry.json"
    calls: list[int] = []

    def downloader(url: str, timeout: int = 120) -> bytes:
        calls.append(1)
        return XLSX_PAYLOAD + b"-" * len(calls)

    times = iter(["2026-11-24T04:00:00Z", "2026-11-24T04:10:00Z"])
    ensure_datasets([_spec()], raw, registry, downloader=downloader, clock=lambda: next(times))
    files = ensure_datasets(
        [_spec()],
        raw,
        registry,
        refresh=True,
        downloader=downloader,
        clock=lambda: next(times),
    )
    assert len(calls) == 2
    assert files[0].retrieved_from == "download"
    assert files[0].downloaded_at_utc == "2026-11-24T04:10:00Z"


def test_local_file_without_registry_is_reported_as_local(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    target = raw / "historico-cbau_es_2024-2026.xlsx"
    target.write_bytes(XLSX_PAYLOAD)
    files = ensure_datasets(
        [_spec(target.name)],
        raw,
        raw / "download-registry.json",
    )
    assert files[0].retrieved_from == "local-file"
    assert files[0].downloaded_at_utc is None
    assert files[0].sha256 == hashlib.sha256(XLSX_PAYLOAD).hexdigest()


def test_offline_mode_fails_when_file_is_missing(tmp_path: Path) -> None:
    with pytest.raises(IngestError, match="Modo sin conexión"):
        ensure_datasets(
            [_spec()],
            tmp_path / "raw",
            tmp_path / "raw" / "download-registry.json",
            offline=True,
        )


def test_html_error_page_is_rejected_and_not_cached(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    with pytest.raises(IngestError, match="HTML"):
        ensure_datasets(
            [_spec()],
            raw,
            raw / "download-registry.json",
            downloader=lambda url, timeout=120: b"<html><body>error</body></html>" * 100,
            clock=lambda: "2026-11-24T04:00:00Z",
        )
    assert not (raw / _spec().filename).exists()


def test_dataset_file_is_immutable_dataclass(tmp_path: Path) -> None:
    entry = DatasetFile(
        spec=_spec(),
        path=tmp_path / "x.xlsx",
        sha256="0" * 64,
        size_bytes=1,
        retrieved_from="local-cache",
        downloaded_at_utc=None,
        verified_at_utc="2026-11-24T04:00:00Z",
    )
    with pytest.raises(AttributeError):
        entry.sha256 = "1" * 64  # type: ignore[misc]
