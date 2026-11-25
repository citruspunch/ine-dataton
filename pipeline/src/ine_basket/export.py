"""Escritura de Parquet, manifiesto de procedencia y JSON para la web."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .build import PipelineResult
from .download import sha256_file


def _atomic_write(path: Path, write: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".part")
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        write(tmp_path)
        tmp_path.replace(path)
    finally:
        tmp_path.unlink(missing_ok=True)


def _write_json(path: Path, payload: Any) -> None:
    def writer(tmp: Path) -> None:
        with tmp.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=1)
            handle.write("\n")

    _atomic_write(path, writer)


def write_outputs(
    result: PipelineResult,
    *,
    processed_dir: Path,
    web_data_dir: Path,
) -> dict[str, Any]:
    """Escribe las tablas Parquet, el manifiesto y el JSON del frontend."""
    processed_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[dict[str, Any]] = []

    for name, frame in result.tables.items():
        path = processed_dir / f"{name}.parquet"
        _atomic_write(
            path, lambda tmp, frame=frame: frame.to_parquet(tmp, index=False, compression="zstd")
        )
        outputs.append(
            {
                "table": name,
                "file": path.name,
                "rows": int(len(frame)),
                "columns": list(frame.columns),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )

    manifest = dict(result.manifest)
    manifest["outputs"] = outputs
    _write_json(processed_dir / "manifest.json", manifest)

    basket_path = web_data_dir / "basket.json"
    _write_json(basket_path, result.web_payload)
    result_tables = {
        "web_payload": {
            "file": basket_path.name,
            "rows": int(len(result.web_payload["ipc"])),
            "bytes": basket_path.stat().st_size,
            "sha256": sha256_file(basket_path),
        }
    }
    return {"manifest": manifest, "web": result_tables}
