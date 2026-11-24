"""Lectura del snapshot público.

Es la única puerta que usan el portal de consulta y el servidor MCP. No conoce
`review_store/`: solo abre archivos dentro de `public_snapshot/`. Si un agregado
no está publicado, devuelve vacío o un error estructurado, nunca una cifra
inventada ni el número de una comparación bloqueada.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import config

NOT_PUBLISHED = "El agregado no está en el snapshot público."


class PublicError(Exception):
    """Error de consulta pública. `code` es estable para clientes MCP."""

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
    """Resuelve una ruta y falla si sale del snapshot público."""
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


def series_catalog(aggregate: dict[str, Any]) -> list[dict[str, Any]]:
    out = []
    for series in aggregate.get("entity", {}).get("series", []):
        out.append(
            {
                "series_id": series["series_id"],
                "label": series.get("label"),
                "base": series.get("base"),
                "unit": series.get("unit"),
                "comparable": series.get("comparable", True),
                "not_comparable_reason": series.get("not_comparable_reason"),
                "has_published_variation": series.get("has_published_variation", False),
                "periods": [p["period"] for p in series.get("points", [])],
            }
        )
    return out


def _series(aggregate: dict[str, Any], series_id: str) -> dict[str, Any] | None:
    for series in aggregate.get("entity", {}).get("series", []):
        if series["series_id"] == series_id:
            return series
    return None


def _point(series: dict[str, Any], period: str) -> dict[str, Any] | None:
    for point in series.get("points", []):
        if point["period"] == period:
            return point
    return None


def _gap(a: str, b: str) -> int:
    ay, am = (int(x) for x in a.split("-"))
    by, bm = (int(x) for x in b.split("-"))
    return (by - ay) * 12 + (bm - am)


def _summary(aggregate: dict[str, Any]) -> dict[str, Any]:
    entity = aggregate.get("entity", {})
    return {
        "case_id": aggregate.get("case_id"),
        "aggregate_title": entity.get("title"),
        "digest": aggregate.get("digest"),
        "aggregate_state": aggregate.get("state"),
        "aggregate_period": (entity.get("display") or {}).get("period"),
        "aggregate_base": (entity.get("display") or {}).get("base"),
    }


def compare(
    case_id: str,
    series_a: str,
    period_a: str,
    series_b: str,
    period_b: str,
    public_dir: Path | None = None,
) -> dict[str, Any]:
    """Comparador seguro. Nunca devuelve un cociente calculado por el prototipo."""
    aggregate = require_aggregate(case_id, public_dir)
    first = _series(aggregate, series_a)
    second = _series(aggregate, series_b)
    if first is None or second is None:
        raise PublicError(
            "serie_desconocida",
            "La serie solicitada no está en el agregado publicado.",
            {"series_a": series_a, "series_b": series_b},
        )

    context = {
        "case_id": case_id,
        "series_a": {"id": first["series_id"], "base": first.get("base")},
        "series_b": {"id": second["series_id"], "base": second.get("base")},
        "period_a": period_a,
        "period_b": period_b,
        **_summary(aggregate),
    }

    if first.get("base") != second.get("base"):
        return {
            "status": "bloqueada",
            "code": "base_incompatible",
            "rule": "IPC-01",
            "message": (
                "Bases distintas: un cociente entre índices de bases distintas no es "
                "una variación. El prototipo no calcula ni muestra ese número."
            ),
            "detail": {
                "base_a": first.get("base"),
                "base_b": second.get("base"),
                "guidance": "Use la serie empalmada oficial para cruzar bases.",
            },
            **context,
        }

    if first["series_id"] != second["series_id"]:
        return {
            "status": "bloqueada",
            "code": "serie_distinta",
            "rule": "IPC-01",
            "message": (
                "Series distintas con la misma base: sus índices no forman una "
                "variación entre sí."
            ),
            **context,
        }

    if not first.get("comparable", True):
        return {
            "status": "bloqueada",
            "code": "serie_no_comparable",
            "rule": "IPC-01",
            "message": first.get("not_comparable_reason")
            or "La serie está marcada como no comparable.",
            **context,
        }

    earlier, later = (
        (period_a, period_b) if period_a <= period_b else (period_b, period_a)
    )
    pa = _point(first, earlier)
    pb = _point(first, later)
    if pa is None or pb is None:
        missing = [p for p in (earlier, later) if _point(first, p) is None]
        return {
            "status": "bloqueada",
            "code": "periodo_no_publicado",
            "rule": "IPC-03",
            "message": "El periodo solicitado no está en el snapshot público habilitado.",
            "detail": {"missing_periods": missing},
            **context,
        }

    gap = _gap(earlier, later)
    if gap == 0:
        return {
            "status": "bloqueada",
            "code": "mismo_periodo",
            "rule": "IPC-02",
            "message": "Los dos periodos son el mismo; no hay variación que mostrar.",
            **context,
        }
    if gap != 1:
        return {
            "status": "bloqueada",
            "code": "periodos_no_contiguos",
            "rule": "IPC-02",
            "message": (
                "Solo se muestra la variación mensual publicada entre meses "
                "consecutivos. Para otros horizontes use la variación interanual o "
                "acumulada oficial."
            ),
            "detail": {"months_between": gap},
            **context,
        }

    published = pb.get("published_variation_pct")
    if published is None:
        return {
            "status": "bloqueada",
            "code": "sin_variacion_publicada",
            "rule": "IPC-03",
            "message": (
                "Este recurso publica índices, no variaciones mensuales. El prototipo "
                "no calcula una variación que el INE no haya publicado."
            ),
            **context,
        }

    return {
        "status": "ok",
        "code": "ok",
        "rule": "IPC-01+IPC-02+IPC-03",
        "message": "Variación mensual publicada por el INE.",
        "series": first["series_id"],
        "series_label": first.get("label"),
        "base": first.get("base"),
        "unit": "porcentaje",
        "period": later,
        "previous_period": earlier,
        "published_pct": published,
        "published_cell": pb.get("variation_cell"),
        "index_value": pb.get("value"),
        "index_cell": pb.get("cell"),
        "previous_index_value": pa.get("value"),
        **_summary(aggregate),
    }


def ipc_aggregates(public_dir: Path | None = None) -> list[dict[str, Any]]:
    out = []
    for entry in list_aggregates(public_dir):
        aggregate = get_aggregate(entry["case_id"], public_dir)
        if not aggregate:
            continue
        if aggregate.get("entity", {}).get("topic") != "ipc":
            continue
        out.append(aggregate)
    return out


def consultar_serie_ipc(
    periodo_inicio: str,
    periodo_fin: str,
    public_dir: Path | None = None,
    series_id: str | None = None,
) -> dict[str, Any]:
    """Serie del IPC publicada entre dos periodos, con sus variaciones oficiales."""
    aggregates = ipc_aggregates(public_dir)
    if not aggregates:
        raise PublicError(
            "no_publicado",
            "No hay ningún agregado del IPC habilitado en el snapshot público.",
        )

    aggregate = None
    series = None
    if series_id is None:
        for candidate in aggregates:
            options = [
                s
                for s in candidate["entity"]["series"]
                if s.get("comparable", True) and s.get("has_published_variation")
            ]
            if options:
                aggregate, series = candidate, options[0]
                break
    else:
        for candidate in aggregates:
            found = _series(candidate, series_id)
            if found:
                aggregate, series = candidate, found
                break

    if aggregate is None or series is None:
        raise PublicError(
            "serie_no_disponible",
            "No hay una serie del IPC con variación publicada en el snapshot público.",
        )

    points = [
        p
        for p in series.get("points", [])
        if periodo_inicio <= p["period"] <= periodo_fin
    ]
    if not points:
        raise PublicError(
            "periodo_no_publicado",
            "El rango solicitado no está en el snapshot público habilitado.",
            {"periodo_inicio": periodo_inicio, "periodo_fin": periodo_fin},
        )

    bases = {p.get("base", series.get("base")) for p in points}
    bases.discard(None)
    if len(bases) > 1:
        raise PublicError(
            "base_incompatible",
            "El rango mezcla bases distintas y no se puede comparar directamente.",
            {"bases": sorted(str(b) for b in bases)},
        )

    return {
        "status": "ok",
        "case_id": aggregate["case_id"],
        "title": aggregate.get("entity", {}).get("title"),
        "series_id": series["series_id"],
        "series_label": series.get("label"),
        "base": series.get("base"),
        "unit": series.get("unit"),
        "periodo_inicio": periodo_inicio,
        "periodo_fin": periodo_fin,
        "digest": aggregate.get("digest"),
        "source_url": aggregate.get("entity", {}).get("source_url"),
        "downloaded_at_utc": aggregate.get("entity", {}).get("downloaded_at_utc"),
        "license": aggregate.get("entity", {}).get("license"),
        "points": [
            {
                "period": p["period"],
                "value": p["value"],
                "cell": p.get("cell"),
                "published_variation_pct": p.get("published_variation_pct"),
                "variation_cell": p.get("variation_cell"),
            }
            for p in points
        ],
        "notice": (
            "Validación técnica del prototipo. La variación mostrada es la publicada "
            "por el INE; el prototipo no la calcula."
        ),
    }


def listar_agregados_habilitados(
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
