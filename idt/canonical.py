"""Serialización canónica y digests reproducibles.

Regla del PRD (7.3 y 7.5): el digest se calcula sobre datos, contrato, perfil,
reglas y hallazgos. Los timestamps de ejecución y de decisión nunca entran.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def canonical_bytes(obj: Any) -> bytes:
    """JSON canónico: claves ordenadas, separadores fijos, UTF-8 sin escapar."""
    return json.dumps(
        obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def digest(obj: Any) -> str:
    return hashlib.sha256(canonical_bytes(obj)).hexdigest()


def text_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def file_sha256(path: Path, chunk_size: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(chunk_size), b""):
            h.update(block)
    return h.hexdigest()
