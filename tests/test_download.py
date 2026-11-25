from __future__ import annotations

import hashlib
import threading
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO

import pytest
from openpyxl import Workbook

from procurement_prices.config import SOURCES, SourceSpec
from procurement_prices.download import DownloadError, acquire_dataset


def _xlsx_bytes() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    for index in range(120):
        sheet.append([f"fila {index}", index, "dato de prueba para que el archivo pese más"])
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


XLSX = _xlsx_bytes()


class Handler(BaseHTTPRequestHandler):
    routes: dict[str, tuple[int, bytes, str]] = {}
    counts: Counter[str] = Counter()

    def do_GET(self) -> None:  # noqa: N802
        self.counts[self.path] += 1
        status, payload, content_type = self.routes.get(
            self.path, (404, b"not found", "text/plain")
        )
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return


@pytest.fixture()
def server():
    Handler.routes = {
        "/data.xlsx": (
            200,
            XLSX,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
        "/file.xlsx": (
            200,
            XLSX,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
        "/captcha.xlsx": (200, b"<!DOCTYPE html><html>CAPTCHA</html>", "text/html"),
    }
    Handler.counts = Counter()
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}", Handler
    finally:
        httpd.shutdown()
        httpd.server_close()


def spec(urls: tuple[str, ...], filename: str = "data.xlsx") -> SourceSpec:
    return SourceSpec(
        id="test-dataset",
        group="DPIR",
        title="Test",
        filename=filename,
        urls=urls,
        source_page="https://datos.ine.gob.gt/dataset/test",
        kind="xlsx",
        publisher="INE",
        license_id="odc-by",
        license_title="ODC-BY",
        license_url="http://www.opendefinition.org/licenses/odc-by",
        status="frozen",
        coverage="test",
        notes="test",
    )


def test_missing_file_is_downloaded_and_hashed(server, tmp_path):
    base, handler = server
    dest = tmp_path / "data.xlsx"
    entry = acquire_dataset(spec((f"{base}/data.xlsx",)), dest=dest)
    assert dest.exists()
    assert entry["retrieval"] == "download"
    assert entry["url"] == f"{base}/data.xlsx"
    assert entry["sha256"] == hashlib.sha256(XLSX).hexdigest()
    assert entry["bytes"] == len(XLSX)
    assert entry["downloadedAtUtc"].endswith("Z")
    assert handler.counts["/data.xlsx"] == 1


def test_cached_file_is_reused_without_network(server, tmp_path):
    base, handler = server
    dest = tmp_path / "data.xlsx"
    first = acquire_dataset(spec((f"{base}/data.xlsx",)), dest=dest)
    second = acquire_dataset(spec((f"{base}/data.xlsx",)), dest=dest)
    assert second["retrieval"] == "local-cache"
    assert second["sha256"] == first["sha256"]
    assert handler.counts["/data.xlsx"] == 1


def test_force_redownloads(server, tmp_path):
    base, handler = server
    dest = tmp_path / "data.xlsx"
    acquire_dataset(spec((f"{base}/data.xlsx",)), dest=dest)
    acquire_dataset(spec((f"{base}/data.xlsx",)), dest=dest, force=True)
    assert handler.counts["/data.xlsx"] == 2


def test_fallback_url_is_recorded(server, tmp_path):
    base, _handler = server
    dest = tmp_path / "data.xlsx"
    entry = acquire_dataset(
        spec((f"{base}/missing.xlsx", f"{base}/file.xlsx")),
        dest=dest,
    )
    assert entry["url"] == f"{base}/file.xlsx"
    assert len(entry["attemptedUrls"]) == 2
    assert entry["attemptedUrls"][0]["status"] == 404
    assert entry["attemptedUrls"][1]["ok"] is True


def test_html_captcha_is_rejected(server, tmp_path):
    base, _handler = server
    with pytest.raises(DownloadError):
        acquire_dataset(spec((f"{base}/captcha.xlsx",)), dest=tmp_path / "data.xlsx")


def test_registry_only_uses_official_ine_hosts():
    for dataset in SOURCES.values():
        for url in dataset.urls:
            assert url.startswith("https://datos.ine.gob.gt/") or url.startswith(
                "https://www.ine.gob.gt/"
            ), f"URL no oficial para {dataset.id}: {url}"
    assert "HISTORICO-OCTUBRE.xlsx" in {dataset.filename for dataset in SOURCES.values()}
