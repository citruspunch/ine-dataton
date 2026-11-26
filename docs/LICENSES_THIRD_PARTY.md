# Licencias de terceros

Generado por `uv run python -m engine.licenses` a partir de los metadatos
instalados. Las licencias del código de este repositorio (MIT) y de los datos
del INE (CC BY) se describen en `README.md`.

## Motor (Python, gestionado con uv)

| Paquete | Versión | Tipo | Licencia |
|---|---|---|---|
| httpx | 0.28.1 | desarrollo | BSD-3-Clause |
| pytest | 9.2.0 | desarrollo | MIT |
| xlwt | 1.3.0 | desarrollo | BSD |
| fastapi | 0.165.0 | directa | MIT |
| mcp | 2.3.0 | directa | MIT |
| openpyxl | 3.1.5 | directa | MIT |
| python-multipart | 0.0.34 | directa | Apache-2.0 |
| PyYAML | 6.0.4 | directa | MIT |
| uvicorn | 0.54.0 | directa | BSD-3-Clause |
| xlrd | 2.0.2 | directa | BSD |
| annotated-doc | 0.0.7 | transitiva | MIT |
| annotated-types | 0.8.0 | transitiva | MIT |
| anyio | 4.16.0 | transitiva | MIT |
| attrs | 26.1.0 | transitiva | MIT |
| certifi | 2026.11.20 | transitiva | MPL-2.0 |
| cffi | 2.1.1 | transitiva | MIT-0 |
| click | 8.5.1 | transitiva | BSD-3-Clause |
| cryptography | 50.0.2 | transitiva | Apache-2.0 OR BSD-3-Clause |
| et_xmlfile | 2.0.0 | transitiva | MIT |
| h11 | 0.16.0 | transitiva | MIT |
| httpcore | 1.0.9 | transitiva | BSD-3-Clause |
| httpcore2 | 2.16.2 | transitiva | BSD-3-Clause |
| httptools | 0.9.0 | transitiva | MIT |
| httpx2 | 2.16.2 | transitiva | BSD-3-Clause |
| idna | 3.20 | transitiva | BSD-3-Clause |
| iniconfig | 2.3.1 | transitiva | MIT |
| jsonschema | 4.26.0 | transitiva | MIT |
| jsonschema-specifications | 2025.9.1 | transitiva | MIT |
| mcp-types | 2.3.0 | transitiva | MIT |
| opentelemetry-api | 1.45.2 | transitiva | Apache-2.0 |
| packaging | 26.4 | transitiva | Apache-2.0 OR BSD-2-Clause |
| pluggy | 1.7.0 | transitiva | MIT |
| pycparser | 3.12 | transitiva | BSD-3-Clause |
| pydantic | 2.14.4 | transitiva | MIT |
| pydantic_core | 2.50.5 | transitiva | MIT |
| Pygments | 2.21.0 | transitiva | BSD-2-Clause |
| PyJWT | 2.15.1 | transitiva | MIT |
| python-dotenv | 1.2.4 | transitiva | BSD-3-Clause |
| referencing | 0.37.0 | transitiva | MIT |
| rpds-py | 2026.9.1 | transitiva | MIT |
| sse-starlette | 3.7.1 | transitiva | BSD-3-Clause |
| starlette | 1.10.0 | transitiva | BSD-3-Clause |
| truststore | 0.10.5 | transitiva | MIT |
| typing-inspection | 0.4.5 | transitiva | MIT |
| typing_extensions | 4.16.0 | transitiva | PSF-2.0 |
| uvloop | 0.23.0 | transitiva | MIT |
| watchfiles | 1.3.0 | transitiva | MIT |
| websockets | 17.4 | transitiva | BSD-3-Clause |

## Interfaz (Node.js, gestionado con pnpm)

| Paquete | Versión | Tipo | Licencia |
|---|---|---|---|
| @tailwindcss/postcss | 4.3.5 | desarrollo | MIT |
| @types/node | 22.20.5 | desarrollo | MIT |
| @types/react | 19.3.0 | desarrollo | MIT |
| @types/react-dom | 19.3.0 | desarrollo | MIT |
| tailwindcss | 4.3.5 | desarrollo | MIT |
| typescript | 5.9.3 | desarrollo | Apache-2.0 |
| @radix-ui/react-dialog | 1.3.1 | directa | MIT |
| class-variance-authority | 0.7.1 | directa | Apache-2.0 |
| clsx | 2.1.1 | directa | MIT |
| lucide-react | 0.475.0 | directa | ISC |
| next | 15.5.29 | directa | MIT |
| react | 19.3.1 | directa | MIT |
| react-dom | 19.3.1 | directa | MIT |
| tailwind-merge | 3.7.1 | directa | MIT |

## Notas

- `kind` distingue dependencias directas, de desarrollo y transitivas.
- Las dependencias Python están declaradas en `pyproject.toml`; las de Node
  en `web/package.json`.
- Esta lista no sustituye los archivos LICENSE de cada paquete, que se
  conservan en el entorno de instalación.
