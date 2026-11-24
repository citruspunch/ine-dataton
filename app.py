#!/usr/bin/env python3
"""Start the local application.

python app.py            # http://127.0.0.1:8000
PORT=9000 python app.py
"""

from __future__ import annotations

import os

import uvicorn

from idt.web.app import app


def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    print(f"INE Data Trust · prototipo en http://{host}:{port}")
    print("  Revisión técnica: /review")
    print("  Consulta pública: /")
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
