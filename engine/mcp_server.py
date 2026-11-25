"""Read-only MCP server over the public snapshot.

Two typed, deterministic tools. No LLM inside the server, no writes and no
access to `stores/review_store/`: every function lives in `engine.public_api`,
which only opens files inside `stores/public_snapshot/`.
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
- No calcula cifras: devuelve la variación publicada por el INE, con su celda.
- Si el cruce mezcla bases o periodos no comparables, devuelve un bloqueo
  estructurado (status "bloqueada") en lugar de un número.
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
    title="Query IPC period comparison",
    description=(
        "Compares two published periods (YYYY-MM) of an IPC series and returns the "
        "variation published by INE. Blocks incompatible bases, non-contiguous "
        "periods and periods outside the enabled snapshot; never invents a figure."
    ),
)
def query_ipc_period_comparison(
    period_a: str,
    period_b: str,
    series: str = "f",
) -> dict[str, Any]:
    aggregates = public_api.ipc_aggregates()
    if not aggregates:
        return {
            "status": "bloqueada",
            "code": "no_publicado",
            "message": "No hay ningún agregado del IPC habilitado en el snapshot público.",
        }
    aggregate = aggregates[0]
    try:
        return public_api.compare(
            aggregate["case_id"], series, period_a, series, period_b
        )
    except public_api.PublicError as exc:
        return exc.to_dict()


def run() -> None:
    server.run(transport="stdio")


if __name__ == "__main__":
    run()
