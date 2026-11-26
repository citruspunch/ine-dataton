# Contratos declarativos (`profiles/`)

Cada archivo `.yaml` de esta carpeta define un contrato para validar archivos
candidatos. Para añadir uno, declare columnas, grano, fechas y el resumen de
variables y unidades. No necesita modificar el código.

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
| `schema` | variables: `name`, `column`, `type`, y opcionales `unit`, `reference`, `nullable`, `notes`, `role` |
| `types` | tipos permitidos en este contrato: `integer`, `float`, `string`, `date` |
| `grain` | columnas que deben ser únicas |
| `dates` | columna de año, mes opcional, formato y periodos esperados |
| `summary_notes` | notas opcionales de cobertura o salvedades del conjunto |

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
  - name: value
    column: "Índice"
    type: float
    unit: índice
    reference: "2024=100"
    notes: Serie principal

types: [integer, float, string]
grain: [year, month]

dates:
  year: year
  month: month
  month_format: name_es      # name_es | number
  expected: ["2025-01", "2025-02"]

summary_notes: >
  Cobertura nacional; no se publican cifras derivadas.
```

`dates` acepta `expected` (lista de `AAAA` o `AAAA-MM`) o `range`
(`from`/`to`). Si no se declara `month`, el contrato es anual.

## Reglas de validación

- Los tipos de `schema` deben pertenecer a `types`, y `types` a la lista permitida.
- `grain`, `dates.year` y, si se declara, `dates.month` deben existir en `schema`.
- `unit`, `reference` y `notes` son texto; `nullable` es booleano.
- Sin `dates.month`, los periodos usan `AAAA`; con mes, `AAAA-MM`. Un `range`
  exige `from` anterior a `to`.
- `CONT-06` resume variables, tipos, unidades, referencias y conteos de valores
  válidos, nulos y excluidos. No compara series.
- Ningún contrato declara filas ni letras de columna: las celdas (`F504`, `G504`)
  se descubren al leer el archivo y solo aparecen como evidencia.
