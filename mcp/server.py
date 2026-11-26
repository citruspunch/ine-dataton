#!/usr/bin/env python3
"""Entry point for the optional P1 MCP server.

    uv run python mcp/server.py

The implementation lives in `engine.mcp_server`; this launcher exists so the
`mcp/` folder from the repository layout is the thing you start. Running the
script (instead of importing the folder as a package) keeps the local `mcp/`
directory from shadowing the official `mcp` SDK.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine.mcp_server import run  # noqa: E402

if __name__ == "__main__":
    run()
