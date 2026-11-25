"""Carga local primero y descarga desde el INE como respaldo.

Regla del PRD: si un archivo requerido ya existe en ``data/raw`` se usa tal
cual; si falta, se descarga de ``datos.ine.gob.gt``, se guarda en caché y se
registra URL exacta, fecha UTC de descarga y hash SHA-256. El registro de
descargas se conserva entre ejecuciones para que el manifiesto siga mostrando
la fecha original aunque el archivo ya esté en caché.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from .errors import IngestError
from .registry import DatasetSpec

RetrievalMode = Literal["download", "local-cache", "local-file"]

_TIMEOUT_SECONDS = 120
_USER_AGENT = "ine-basket/1.0 (Dataton INE 2026; simulador CBA; +https://ine.gob.gt)"


def utc_now_iso() -> str:
    """Marca de tiempo UTC en ISO 8601 con segundos y sufijo ``Z``."""
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _default_downloader(
    url: str,
    timeout: int = _TIMEOUT_SECONDS,
    *,
    attempts: int = 3,
) -> bytes:
    """Descarga con reintentos breves para tolerar fallas transitorias del portal."""
    import requests

    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            response = requests.get(
                url,
                timeout=timeout,
                headers={"User-Agent": _USER_AGENT, "Accept": "*/*"},
            )
            response.raise_for_status()
            return response.content
        except requests.RequestException as exc:  # pragma: no cover - red real
            last_error = exc
            if attempt < attempts:
                time.sleep(1.5 * attempt)
    raise last_error  # type: ignore[misc]


def _validate_payload(data: bytes, spec: DatasetSpec) -> None:
    """Evita guardar páginas de error HTML o archivos truncados como si fueran datos."""
    if len(data) < 1024:
        raise IngestError(
            f"{spec.filename}: descarga demasiado pequeña ({len(data)} bytes); "
            "posible página de error del portal."
        )
    head = data[:512].lstrip().lower()
    if head.startswith(b"<") or b"<html" in head:
        raise IngestError(
            f"{spec.filename}: el servidor devolvió HTML en lugar de la hoja de cálculo."
        )
    if spec.extension == "xlsx" and not data.startswith(b"PK"):
        raise IngestError(f"{spec.filename}: el contenido no es un XLSX (falta firma ZIP).")
    if spec.extension == "xls" and not data.startswith(b"\xd0\xcf\x11\xe0"):
        raise IngestError(f"{spec.filename}: el contenido no es un XLS antiguo (OLE2).")


@dataclass(slots=True, frozen=True)
class DatasetFile:
    """Resultado de resolver un archivo: ruta local más su procedencia."""

    spec: DatasetSpec
    path: Path
    sha256: str
    size_bytes: int
    retrieved_from: RetrievalMode
    downloaded_at_utc: str | None
    verified_at_utc: str

    def manifest_entry(self, repo_root: Path) -> dict:
        spec = self.spec
        try:
            local_path = self.path.relative_to(repo_root).as_posix()
        except ValueError:
            local_path = self.path.as_posix()
        return {
            "key": spec.key,
            "filename": spec.filename,
            "local_path": local_path,
            "title": spec.title,
            "role": spec.role,
            "coverage": spec.coverage,
            "source_url": spec.url,
            "retrieved_from": self.retrieved_from,
            "downloaded_at_utc": self.downloaded_at_utc,
            "verified_at_utc": self.verified_at_utc,
            "bytes": self.size_bytes,
            "sha256": self.sha256,
            "license": {
                "status": spec.license_status,
                "id": spec.license_id,
                "title": spec.license_title,
                "url": spec.license_url,
            },
            "ckan": {
                "portal": "datos.ine.gob.gt",
                "package_id": spec.package_id,
                "package_name": spec.package_name,
                "package_title": spec.package_title,
                "package_url": spec.package_url,
                "resource_id": spec.resource_id,
                "resource_last_modified_utc": spec.resource_last_modified_utc,
            },
            "notes": spec.notes,
        }


class DownloadRegistry:
    """Registro persistente de descargas (``data/raw/download-registry.json``)."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.files: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - archivo corrupto
            raise IngestError(f"Registro de descargas corrupto: {self.path}") from exc
        if isinstance(payload, dict) and isinstance(payload.get("files"), dict):
            self.files = payload["files"]

    def get(self, filename: str) -> dict | None:
        return self.files.get(filename)

    def record(
        self,
        spec: DatasetSpec,
        *,
        sha256: str,
        size_bytes: int,
        downloaded_at_utc: str,
    ) -> None:
        previous = self.files.get(spec.filename) or {}
        self.files[spec.filename] = {
            "url": spec.url,
            "sha256": sha256,
            "bytes": size_bytes,
            # Conserva la primera descarga conocida; actualiza la última.
            "first_downloaded_at_utc": previous.get("first_downloaded_at_utc", downloaded_at_utc),
            "downloaded_at_utc": downloaded_at_utc,
        }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"schema_version": 1, "files": self.files}
        _atomic_write_text(self.path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".part")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        Path(tmp_name).replace(path)
    finally:
        tmp = Path(tmp_name)
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def _atomic_write_text(path: Path, text: str) -> None:
    _atomic_write_bytes(path, text.encode("utf-8"))


def ensure_dataset(
    spec: DatasetSpec,
    raw_dir: Path,
    registry: DownloadRegistry,
    *,
    refresh: bool = False,
    offline: bool = False,
    downloader: Callable[..., bytes] | None = None,
    clock: Callable[[], str] = utc_now_iso,
) -> DatasetFile:
    """Resuelve un archivo: caché local si existe, descarga si falta o se fuerza."""
    path = raw_dir / spec.filename
    verified_at = clock()

    if path.exists() and not refresh:
        digest = sha256_file(path)
        size = path.stat().st_size
        record = registry.get(spec.filename)
        if record and record.get("sha256") == digest:
            return DatasetFile(
                spec=spec,
                path=path,
                sha256=digest,
                size_bytes=size,
                retrieved_from="local-cache",
                downloaded_at_utc=record.get("downloaded_at_utc"),
                verified_at_utc=verified_at,
            )
        # Archivo presente sin registro previo (p. ej. copiado a mano).
        return DatasetFile(
            spec=spec,
            path=path,
            sha256=digest,
            size_bytes=size,
            retrieved_from="local-file",
            downloaded_at_utc=None,
            verified_at_utc=verified_at,
        )

    if offline:
        raise IngestError(
            f"Modo sin conexión: falta {spec.filename} en {raw_dir}. "
            f"Descárguelo de {spec.url} y vuelva a ejecutar."
        )

    fetch = downloader or _default_downloader
    try:
        payload = fetch(spec.url)
    except Exception as exc:  # noqa: BLE001 - se re-empaqueta con contexto
        raise IngestError(
            f"No fue posible descargar {spec.filename} desde {spec.url}: {exc}"
        ) from exc

    _validate_payload(payload, spec)
    _atomic_write_bytes(path, payload)
    digest = sha256_file(path)
    size = path.stat().st_size
    registry.record(
        spec,
        sha256=digest,
        size_bytes=size,
        downloaded_at_utc=verified_at,
    )
    return DatasetFile(
        spec=spec,
        path=path,
        sha256=digest,
        size_bytes=size,
        retrieved_from="download",
        downloaded_at_utc=verified_at,
        verified_at_utc=verified_at,
    )


def ensure_datasets(
    specs: Sequence[DatasetSpec],
    raw_dir: Path,
    registry_path: Path,
    *,
    refresh: bool = False,
    offline: bool = False,
    downloader: Callable[..., bytes] | None = None,
    clock: Callable[[], str] = utc_now_iso,
) -> list[DatasetFile]:
    """Resuelve una lista de archivos y persiste el registro de descargas."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    registry = DownloadRegistry(registry_path)
    resolved: list[DatasetFile] = []
    try:
        for spec in specs:
            resolved.append(
                ensure_dataset(
                    spec,
                    raw_dir,
                    registry,
                    refresh=refresh,
                    offline=offline,
                    downloader=downloader,
                    clock=clock,
                )
            )
            # Guarda tras cada archivo: una falla posterior no pierde la
            # procedencia de lo que ya se descargó.
            registry.save()
    finally:
        registry.save()
    return resolved


def iter_local_missing(specs: Iterable[DatasetSpec], raw_dir: Path) -> list[DatasetSpec]:
    """Archivos requeridos que no están en la carpeta local."""
    return [spec for spec in specs if not (raw_dir / spec.filename).exists()]
