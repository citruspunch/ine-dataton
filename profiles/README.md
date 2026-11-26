# Contratos declarativos (`profiles/`)

Cada archivo `.yaml` de esta carpeta define un contrato para validar archivos
candidatos. Para añadir uno, declare columnas, grano, fechas y comparabilidad.
No necesita modificar el código.

El validador está en `engine/profiles.py` y se puede ejecutar sin la interfaz:

```bash
uv run python -m engine.profiles                      # valida todos los contratos
uv run python -m engine.profiles profiles/mi_contrato.yaml
```

La interfaz aplica la misma validación al guardar desde **Nueva regla**, donde un
formulario guiado construye el YAML y devuelve errores por campo (`schema[2].type`,
`dates.expected[0]`, …).

## Campos obligatorios

| Campo | Qué declara |
|---|---|
| `profile_id` | identificador único (minúsculas, dígitos, guion bajo) |
| `version` | versión del contrato; entra en el digest |
| `kind` | `xlsx`, `delimited` o `pair` |
| `title` | nombre legible |
| `expected_sheet` | hoja declarada (obligatoria en XLSX, `null` en CSV) |
| `header_row` | fila de encabezado, 1 o mayor |
| `schema` | columnas: `name`, `column`, `type`, y opcional `role`/`nullable` |
| `types` | tipos permitidos en este contrato: `integer`, `float`, `string`, `date` |
| `grain` | columnas que deben ser únicas |
| `dates` | columnas de año y mes, formato y periodos esperados |
| `comparability` | unidad y series publicables |

## Ejemplo mínimo

```yaml
profile_id: mi_contrato_v1
version: "1.0.0"
kind: xlsx
title: Mi contrato
expected_sheet: Hoja1
header_row: 1

schema:
  - { name: year, column: "Año", type: integer }
  - { name: month, column: "Mes", type: string }
  - { name: value, column: "Índice", type: float }

types: [integer, float, string]
grain: [year, month]

dates:
  year: year
  month: month
  month_format: name_es      # name_es | number
  expected: ["2025-01", "2025-02"]

comparability:
  unit: índice
  series:
    - { id: serie, label: "Serie principal", index: value, base: "2024=100" }
  checks: []
```

`dates` acepta `expected` (lista de `AAAA-MM`) o `range` (`from`/`to`).

## Reglas de validación

- Los tipos de `schema` deben pertenecer a `types`, y `types` a la lista permitida.
- `grain`, `dates.year`, `dates.month` y cada `comparability.series[].index` deben
  existir en `schema`.
- Los periodos usan `AAAA-MM`; un `range` exige `from` anterior a `to`.
- Ningún contrato declara filas ni letras de columna: las celdas (`F504`, `G504`)
  se descubren al leer el archivo y solo aparecen como evidencia.
