"""Reading of the public snapshot.

This is the only door used by the consultation portal and the MCP server. It
does not know about `review_store/`: it only opens files inside
`public_snapshot/`. If an aggregate is not published it returns nothing or a
structured error, never an invented figure.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import config

NOT_PUBLISHED = "El agregado no está en el snapshot público."


class PublicError(Exception):
    """Public query error. `code` is stable for MCP clients."""

    def __init__(
        self, code: str, message: str, detail: dict[str, Any] | None = None
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.detail = detail or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "bloqueada",
            "code": self.code,
            "message": self.message,
            **self.detail,
        }


def _public_dir(public_dir: Path | None = None) -> Path:
    return Path(public_dir) if public_dir else config.PUBLIC_DIR


def _safe(root: Path, *parts: str) -> Path:
    """Resolve a path and fail if it leaves the public snapshot."""
    base = Path(root).resolve()
    path = base.joinpath(*parts).resolve()
    if path != base and base not in path.parents:
        raise PublicError(
            "acceso_denegado",
            "La ruta solicitada está fuera del snapshot público.",
            {"requested": str(parts)},
        )
    return path


def load_index(public_dir: Path | None = None) -> dict[str, Any]:
    path = _safe(_public_dir(public_dir), "index.json")
    if not path.exists():
        return {"snapshot_id": None, "aggregates": []}
    return json.loads(path.read_text(encoding="utf-8"))


def list_aggregates(public_dir: Path | None = None) -> list[dict[str, Any]]:
    return list(load_index(public_dir).get("aggregates", []))


def get_aggregate(
    case_id: str, public_dir: Path | None = None
) -> dict[str, Any] | None:
    if not case_id or "/" in case_id or ".." in case_id or "\\" in case_id:
        return None
    path = _safe(_public_dir(public_dir), "aggregates", f"{case_id}.json")
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def require_aggregate(case_id: str, public_dir: Path | None = None) -> dict[str, Any]:
    aggregate = get_aggregate(case_id, public_dir)
    if aggregate is None:
        raise PublicError("no_publicado", NOT_PUBLISHED, {"case_id": case_id})
    return aggregate


def get_receipt(case_id: str, public_dir: Path | None = None) -> dict[str, Any] | None:
    if not case_id or "/" in case_id or ".." in case_id or "\\" in case_id:
        return None
    path = _safe(_public_dir(public_dir), "receipts", f"{case_id}.json")
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def list_enabled_aggregates(
    public_dir: Path | None = None,
) -> list[dict[str, Any]]:
    out = []
    for entry in list_aggregates(public_dir):
        aggregate = get_aggregate(entry["case_id"], public_dir)
        if not aggregate:
            continue
        entity = aggregate.get("entity", {})
        display = entity.get("display") or {}
        license_info = entity.get("license") or {}
        out.append(
            {
                "case_id": aggregate["case_id"],
                "title": entity.get("title") or aggregate.get("label"),
                "state": aggregate.get("state"),
                "state_text": aggregate.get("state_text"),
                "topic": entity.get("topic"),
                "period": display.get("period"),
                "base": display.get("base"),
                "unit": display.get("unit"),
                "source_url": entity.get("source_url"),
                "downloaded_at_utc": entity.get("downloaded_at_utc"),
                "license": {
                    "id": license_info.get("id"),
                    "attribution": license_info.get("attribution"),
                },
                "sha256": entity.get("sha256"),
                "decision_basis_digest": aggregate.get("digest"),
                "published_at_utc": aggregate.get("published_at_utc"),
                "series": [
                    {
                        "series_id": s["series_id"],
                        "label": s.get("label"),
                        "base": s.get("base"),
                        "comparable": s.get("comparable", True),
                        "periods": [p["period"] for p in s.get("points", [])],
                    }
                    for s in entity.get("series", [])
                ],
            }
        )
    return out
