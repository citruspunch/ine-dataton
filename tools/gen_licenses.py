#!/usr/bin/env python3
"""Generate LICENSES_THIRD_PARTY.md from the installed metadata.

It does not invent licenses: it reads `License-Expression`, `License` and the
package classifiers. If a package declares none, it says so.
"""

from __future__ import annotations

import importlib.metadata as md
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "LICENSES_THIRD_PARTY.md"

DIRECT = [
    "fastapi",
    "uvicorn",
    "jinja2",
    "python-multipart",
    "PyYAML",
    "openpyxl",
    "mcp",
]
DEV = ["pytest", "httpx"]
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


def license_of(dist: md.Distribution) -> str:
    meta = dist.metadata
    expression = meta.get("License-Expression")
    if expression:
        return expression
    raw = (meta.get("License") or "").strip()
    if raw and len(raw) < 60 and "\n" not in raw:
        return LICENSE_ALIASES.get(raw, raw)
    for classifier in meta.get_all("Classifier") or []:
        if classifier.startswith("License ::"):
            parts = [p.strip() for p in classifier.split("::")]
            return LICENSE_ALIASES.get(parts[-1], parts[-1])
    if raw:
        first = raw.splitlines()[0].strip()
        return LICENSE_ALIASES.get(first, first[:60])
    return "no declarada"


def home_page(dist: md.Distribution) -> str:
    meta = dist.metadata
    for key in ("Home-page", "Project-URL"):
        values = meta.get_all(key) or []
        for value in values:
            if key == "Home-page" and value:
                return value
        for value in values:
            url = value.split(",", 1)[-1].strip()
            if url.startswith("http"):
                return url
    return ""


def main() -> int:
    rows = []
    direct = {name.lower() for name in DIRECT}
    dev = {name.lower() for name in DEV}
    for dist in md.distributions():
        name = dist.metadata["Name"]
        if not name or name.lower() in SKIP:
            continue
        rows.append(
            {
                "name": name,
                "version": dist.version,
                "license": license_of(dist),
                "kind": "directa"
                if name.lower() in direct
                else "desarrollo"
                if name.lower() in dev
                else "transitiva",
                "url": home_page(dist),
            }
        )
    rows.sort(key=lambda r: (r["kind"], r["name"].lower()))

    lines = [
        "# Licencias de terceros",
        "",
        "Generado por `tools/gen_licenses.py` a partir de los metadatos instalados en",
        "el entorno virtual. Las licencias del código de este repositorio (MIT) y de",
        "los datos del INE (CC BY) se describen en el `README.md`.",
        "",
        "| Paquete | Versión | Tipo | Licencia | Enlace |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        url = f"[{row['url']}]({row['url']})" if row["url"] else ""
        lines.append(
            f"| {row['name']} | {row['version']} | {row['kind']} | {row['license']} | {url} |"
        )
    lines += [
        "",
        "## Notas",
        "",
        "- `kind` distingue dependencias directas del producto, de desarrollo y",
        "  transitivas arrastradas por ellas.",
        "- Las dependencias directas están fijadas en `requirements.txt`; las de",
        "  desarrollo, en `requirements-dev.txt`.",
        "- Esta lista no sustituye los archivos LICENSE de cada paquete, que se",
        "  conservan en el entorno de instalación.",
        "",
    ]
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"escrito {OUTPUT.name} con {len(rows)} paquetes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
