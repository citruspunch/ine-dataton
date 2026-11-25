"""Read-only MCP server over the public snapshot (optional P1).

Two typed, deterministic tools: enabled aggregates and aggregate
metadata/receipt lookup. No LLM inside the server, no writes, no period
comparison logic and no access to `stores/review_store/`: every function lives
in `engine.public_api`, which only opens files inside `stores/public_snapshot/`.
"""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from . import public_api

INSTRUCTIONS = """
Herramientas de solo lectura sobre agregados del INE ya validados y habilitados.

Reglas del servidor:
- Solo lee el snapshot público. No tiene acceso a la cola de revisión,
  candidatos ni fixtures.
- No calcula cifras ni compara periodos: devuelve metadatos y el recibo
  publicado, con la fuente y el digest de la decisión.
- Si un agregado no está habilitado, devuelve un bloqueo estructurado.
""".strip()

server = MCPServer(name="ine-data-trust", instructions=INSTRUCTIONS)


@server.tool(
    title="List enabled aggregates",
    description=(
        "Lists the aggregates in the public snapshot with source, official URL, "
        "UTC download date, license, base, series and decision_basis_digest."
    ),
)
def list_enabled_aggregates() -> dict[str, Any]:
    aggregates = public_api.list_enabled_aggregates()
    index = public_api.load_index()
    return {
        "snapshot_id": index.get("snapshot_id"),
        "total": len(aggregates),
        "aggregates": aggregates,
        "notice": (
            "Solo agregados habilitados tras el gate humano. El prototipo no certifica."
        ),
    }


@server.tool(
    title="Get aggregate receipt",
    description=(
        "Returns the metadata and the public receipt of one enabled aggregate: "
        "source, official URL, UTC download date, license, base, period, series, "
        "validation digest and the recorded human decision. Read-only; it returns "
        "no computed figure."
    ),
)
def get_aggregate_receipt(case_id: str) -> dict[str, Any]:
    aggregate = public_api.get_aggregate(case_id)
    if aggregate is None:
        return {
            "status": "bloqueada",
            "code": "no_publicado",
            "message": "El agregado no está en el snapshot público.",
            "case_id": case_id,
        }

    entity = aggregate.get("entity", {})
    display = entity.get("display") or {}
    license_info = entity.get("license") or {}
    series = entity.get("series") or []

    metadata = {
        "case_id": aggregate.get("case_id"),
        "title": entity.get("title") or aggregate.get("label"),
        "state": aggregate.get("state"),
        "state_text": aggregate.get("state_text"),
        "period": display.get("period"),
        "base": display.get("base"),
        "unit": display.get("unit"),
        "source_url": entity.get("source_url"),
        "downloaded_at_utc": entity.get("downloaded_at_utc"),
        "published_at_utc": aggregate.get("published_at_utc"),
        "sha256": entity.get("sha256"),
        "license": {
            "id": license_info.get("id"),
            "attribution": license_info.get("attribution"),
        },
        "decision_basis_digest": aggregate.get("digest"),
        "series": [
            {
                "series_id": item.get("series_id"),
                "label": item.get("label"),
                "base": item.get("base"),
                "unit": item.get("unit"),
                "periods": len(item.get("points") or []),
            }
            for item in series
        ],
    }

    return {
        "status": "ok",
        "case_id": aggregate.get("case_id"),
        "metadata": metadata,
        "receipt": public_api.get_receipt(case_id),
        "notice": (
            "Validación técnica del prototipo. El recibo separa technical_payload y "
            "decision_log; el digest no incluye timestamps."
        ),
    }


def run() -> None:
    server.run(transport="stdio")


if __name__ == "__main__":
    run()
