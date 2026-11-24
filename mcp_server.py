#!/usr/bin/env python3
"""Servidor MCP de solo lectura sobre el snapshot público.

Dos herramientas tipadas y deterministas. No hay LLM dentro del servidor, no hay
escritura y no hay acceso a `review_store/`: todas las funciones viven en
`idt.public_api`, que solo abre archivos dentro de `public_snapshot/`.

    python mcp_server.py
"""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver import MCPServer

from idt import public_api

INSTRUCTIONS = """
Herramientas de solo lectura sobre agregados del INE ya validados y habilitados.

Reglas del servidor:
- Solo lee public_snapshot/. No tiene acceso a review_store/, candidatos ni fixtures.
- No calcula cifras: devuelve la variación publicada por el INE, con su celda.
- Si el cruce mezcla bases o periodos no comparables, devuelve un bloqueo
  estructurado (status "bloqueada") en lugar de un número.
""".strip()

server = MCPServer(name="ine-data-trust", instructions=INSTRUCTIONS)


@server.tool(
    title="Listar agregados habilitados",
    description=(
        "Lista los agregados del snapshot público con fuente, URL oficial, fecha de "
        "descarga UTC, licencia, base, series y decision_basis_digest."
    ),
)
def listar_agregados_habilitados() -> dict[str, Any]:
    aggregates = public_api.listar_agregados_habilitados()
    index = public_api.load_index()
    return {
        "snapshot_id": index.get("snapshot_id"),
        "total": len(aggregates),
        "agregados": aggregates,
        "notice": (
            "Solo agregados habilitados tras el gate humano. El prototipo no certifica."
        ),
    }


@server.tool(
    title="Consultar serie del IPC",
    description=(
        "Devuelve los puntos del IPC publicados entre dos periodos (formato AAAA-MM) "
        "con la variación mensual publicada por el INE. Si el rango cruza bases "
        "incompatibles o sale del snapshot habilitado, devuelve un bloqueo "
        "estructurado sin inventar cifras."
    ),
)
def consultar_serie_ipc(periodo_inicio: str, periodo_fin: str) -> dict[str, Any]:
    try:
        return public_api.consultar_serie_ipc(periodo_inicio, periodo_fin)
    except public_api.PublicError as exc:
        return exc.to_dict()


if __name__ == "__main__":
    server.run(transport="stdio")
