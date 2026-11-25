#!/usr/bin/env python3
"""Generate docs/LICENSES_THIRD_PARTY.md from installed metadata.

It does not invent licenses: for Python it reads `License-Expression`,
`License` and the classifiers; for Node it reads each package's `license`
field. If a package declares none, it says so.
"""

from __future__ import annotations

import importlib.metadata as md
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = ROOT / "web"
OUTPUT = ROOT / "docs" / "LICENSES_THIRD_PARTY.md"

PYTHON_DIRECT = [
    "fastapi",
    "uvicorn",
    "python-multipart",
    "PyYAML",
    "openpyxl",
    "xlrd",
    "mcp",
]
PYTHON_DEV = ["pytest", "httpx", "xlwt"]
SKIP = {"pip", "setuptools", "wheel", "pkg-resources"}

LICENSE_ALIASES = {
    "MIT License": "MIT",
    "MIT": "MIT",
    "BSD License": "BSD",
    "BSD-3-Clause": "BSD-3-Clause",
    "Apache Software License": "Apache-2.0",
    "Apache-2.0": "Apache-2.0",
    "Python Software Foundation License": "PSF-2.0",
    "ISC License (ISCL)": "ISC",
    "Mozilla Public License 2.0 (MPL 2.0)": "MPL-2.0",
}


def python_license(dist: md.Distribution) -> str:
    meta = dist.metadata
    expression = meta.get("License-Expression")
    if expression:
        return expression
    raw = (meta.get("License") or "").strip()
    if raw and len(raw) < 60 and "\n" not in raw:
        return LICENSE_ALIASES.get(raw, raw)
    for classifier in meta.get_all("Classifier") or []:
        if classifier.startswith("License ::"):
            parts = [part.strip() for part in classifier.split("::")]
            return LICENSE_ALIASES.get(parts[-1], parts[-1])
    if raw:
        first = raw.splitlines()[0].strip()
        return LICENSE_ALIASES.get(first, first[:60])
    return "no declarada"


def python_rows() -> list[dict[str, str]]:
    direct = {name.lower() for name in PYTHON_DIRECT}
    dev = {name.lower() for name in PYTHON_DEV}
    rows = []
    for dist in md.distributions():
        name = dist.metadata["Name"]
        if not name or name.lower() in SKIP:
            continue
        rows.append(
            {
                "name": name,
                "version": dist.version,
                "license": python_license(dist),
                "kind": "directa"
                if name.lower() in direct
                else "desarrollo"
                if name.lower() in dev
                else "transitiva",
            }
        )
    rows.sort(key=lambda row: (row["kind"], row["name"].lower()))
    return rows


def node_rows() -> list[dict[str, str]]:
    package_json = WEB_DIR / "package.json"
    if not package_json.exists():
        return []
    manifest = json.loads(package_json.read_text(encoding="utf-8"))
    names = {
        **{name: "directa" for name in manifest.get("dependencies", {})},
        **{name: "desarrollo" for name in manifest.get("devDependencies", {})},
    }
    rows = []
    for name, kind in names.items():
        meta_path = WEB_DIR / "node_modules" / name / "package.json"
        if not meta_path.exists():
            continue
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        declared = meta.get("license") or meta.get("licenses") or "no declarada"
        if isinstance(declared, list):
            declared = ", ".join(
                item.get("type", "?") if isinstance(item, dict) else str(item)
                for item in declared
            )
        elif isinstance(declared, dict):
            declared = declared.get("type", "no declarada")
        rows.append(
            {
                "name": name,
                "version": str(meta.get("version", "")),
                "license": str(declared),
                "kind": kind,
            }
        )
    rows.sort(key=lambda row: (row["kind"], row["name"].lower()))
    return rows


def table(rows: list[dict[str, str]]) -> list[str]:
    lines = ["| Paquete | Versión | Tipo | Licencia |", "|---|---|---|---|"]
    for row in rows:
        lines.append(
            f"| {row['name']} | {row['version']} | {row['kind']} | {row['license']} |"
        )
    return lines


def main() -> int:
    python = python_rows()
    node = node_rows()
    lines = [
        "# Licencias de terceros",
        "",
        "Generado por `uv run python -m engine.licenses` a partir de los metadatos",
        "instalados. Las licencias del código de este repositorio (MIT) y de los datos",
        "del INE (CC BY) se describen en `README.md`.",
        "",
        "## Motor (Python, gestionado con uv)",
        "",
        *table(python),
        "",
        "## Interfaz (Node.js, gestionado con pnpm)",
        "",
        *table(node),
        "",
        "## Notas",
        "",
        "- `kind` distingue dependencias directas, de desarrollo y transitivas.",
        "- Las dependencias Python están declaradas en `pyproject.toml`; las de Node",
        "  en `web/package.json`.",
        "- Esta lista no sustituye los archivos LICENSE de cada paquete, que se",
        "  conservan en el entorno de instalación.",
        "",
    ]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(
        f"escrito {OUTPUT.relative_to(ROOT)} con {len(python)} paquetes Python y {len(node)} de Node"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
