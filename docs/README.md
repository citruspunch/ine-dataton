# INE Data Trust

Validación técnica de agregados estadísticos ya publicados. El sistema comprueba
un archivo candidato contra un contrato declarativo en YAML, marca identidades
incompatibles por SHA-256, bloquea comparaciones entre bases del IPC que no son
comparables, registra el visto bueno humano y exporta un recibo reproducible.

> **No implica certificación, aprobación ni adopción por el INE.**
> Datatón INE 2026, Categoría 2. Versión 2.0.

---

## 1. Problema y usuarios

Un agregado candidato puede parecer correcto y no ser comparable con su versión
oficial por **base, periodo, unidad, esquema, identidad o licencia**.

- **Usuario primario:** técnico de publicaciones que revisa un agregado al lado de
  la ficha oficial, dentro del flujo del **procedimiento 18** del Manual de
  procesos de la Dirección de Informática del INE.
- **Usuario secundario:** periodista o analista que necesita fuente, base y
  periodo, y una negativa clara cuando pide comparar cosas que no se comparan.

El producto entrega **estado, severidad, cobertura y recibo**. No entrega un
puntaje de 0 a 100 y no certifica.

## 2. Arranque

Requisitos: **uv** (Python) y **pnpm** (Node.js). No se usa `make`.

```bash
uv sync                       # entorno Python y uv.lock
pnpm --dir web install        # interfaz Next.js y pnpm-lock.yaml
pnpm run prepare              # verifica y registra las muestras del INE
pnpm run dev                  # motor :8000 + interfaz en el siguiente puerto libre
```

Abrir la URL que imprime el arranque (**http://127.0.0.1:3000** si está libre).
El portal de consulta arranca vacío: un agregado solo aparece cuando un revisor
lo valida y registra el visto bueno en la bandeja de revisión.

Scripts disponibles (definidos en `package.json`):

| Script | Qué hace |
|---|---|
| `pnpm run dev` | arranca motor y web juntos |
| `pnpm run dev:engine` | solo el motor (`uv run uvicorn engine.api:app`) |
| `pnpm run dev:web` | solo la interfaz (`next dev`) |
| `pnpm run prepare` | verifica las muestras del INE y escribe el manifiesto |
| `pnpm run verify` | recalcula digests y retira agregados sin decisión vigente |
| `pnpm run test:engine` | suite `pytest` |
| `pnpm run test:web` | verificación de tipos de TypeScript |
| `pnpm run mcp` | servidor MCP por stdio |
| `pnpm run profiles:check` | valida los contratos YAML de `profiles/` |

Después de `uv sync` y `pnpm install`, todo funciona **sin red**. Los contratos
se pueden validar sin interfaz con `uv run python -m engine.profiles`.

> La cola de revisión arranca sin decisiones: los recursos registrados y los
> archivos que se cargan se validan y se habilitan desde la interfaz, y cada
> decisión queda en la bitácora con responsable y motivo.

## 3. Arquitectura de carpetas

```text
web/                  Next.js + TypeScript + Tailwind + shadcn/ui
engine/               núcleo determinista en Python (uv)
mcp/                  lanzador del servidor MCP de solo lectura
profiles/             contratos declarativos YAML
rules/                registro de reglas versionadas
data/                 muestras INE verificadas y manifiesto del snapshot
stores/
  review_store/       cola privada: candidatos, recibos, decisiones
  public_snapshot/    agregados habilitados, recibos públicos, vista de consulta
tests/                pytest (motor y API) y verificación de tipos
docs/                 README, licencias de terceros, nota de IA
scripts/              arranque conjunto de servidores (Node)
```

- **`engine/`** no importa nada de `web/`. Expone una API HTTP local
  (`engine/api.py`) que la interfaz consume; toda la decisión vive en Python.
- **`web/`** solo renderiza y recoge datos. No valida ni decide.
- **`stores/review_store/`** es privado: cargas, recibos privados,
  bitácora de decisiones y enmiendas de simulación.
- **`stores/public_snapshot/`** solo recibe agregados habilitados tras el gate.

## 4. Datasets reales utilizados

Ambos del conjunto CKAN **IPC Base Anual 2024=100**
(`dataset_id 4243818d-b479-4bc1-aae6-2735e2b51265`), licencia `cc-by`.

| Recurso | Archivo | Descarga (UTC) | Bytes | SHA-256 |
|---|---|---|---|---|
| Empalme del IPC por República | `data/ipc_emprepu_es25.xlsx` | 2026-11-24T05:41:54Z | 68.016 | `d0101e366ee6d6bb02345db64b8c725c0a4c65ee85aa800d751d41b8381664d4` |
| IPC por Región | `data/ipc_porreg_es25.xlsx` | 2026-11-24T19:34:21Z | 12.703 | `841dada98d20bca5ec8c23755ac8d793ce76b2e06dc7c82d34fc4f48475c8c1e` |

URLs completas en `data/sources.json` y `data/manifest.json`.

**Por qué el empalme.** Permite exponer un error metodológico real y
verificable:

| Celda | Valor | Qué es |
|---|---|---|
| `E503` | 101,702855 | índice base diciembre 2023=100 |
| `F503` | 100,513541 | índice base 2024=100 |
| `F504` | 101,017579 | índice base 2024=100 |
| `G504` | 0,501463 % | variación mensual **publicada** |

- `F504 / F503` es válido: misma base, meses contiguos → **+0,501463 %**, que
  coincide con `G504`. La ficha muestra la cifra publicada, no una calculada.
- `F504 / E503` es **inválido**: mezcla bases. Da `−0,673802 %`. Ese número solo
  aparece en la pantalla privada de revisión: **no entra** al snapshot público,
  ni al export, ni a la ficha. Hay tests que lo verifican.

**Por qué el regional.** Segundo recurso real con otra forma: tabla ancha (una
columna por región), hoja `Hoja1`, sin variación publicada y con un rango de
periodos (2025-01 a 2026-10). Se evalúa con el mismo motor y un perfil distinto.

## 5. Perfiles declarativos y reglas

Los perfiles son YAML y **no declaran coordenadas**:

```yaml
expected_sheet: Hoja2
header_row: 1
schema:
  - { name: f_index, column: "Índice año Base  2024=100.00 d/", type: float }
grain: [year, month]
dates: { year: year, month: month, month_format: name_es, expected: ["2024-12", "2025-01"] }
comparability:
  unit: índice
  series:
    - { id: f, index: f_index, base: "2024=100", variation: g_monthly, comparable: true }
  checks:
    - id: mensual_ene_2025
      numerator:   { field: f_index, period: "2025-01" }
      denominator: { field: f_index, period: "2024-12" }
      published:   { field: g_monthly, period: "2025-01" }
```

Campos obligatorios: `profile_id`, `version`, `kind`, `title`, `expected_sheet`,
`header_row`, `schema`, `types`, `grain`, `dates`, `comparability`. Tipos
permitidos: `integer`, `float`, `string`, `date`.

Las columnas se resuelven por **encabezado** y los periodos por **año y mes**; las
celdas (`F504`, `G504`) se descubren al leer y solo aparecen como metadato en la
evidencia. Un test recorre los YAML y falla si alguien escribe `letter`, `cell` o
`row_number`.

Reglas versionadas en `rules/rules.json`: `SNAP-01` integridad, `LIC-01` licencia,
`CONT-01`…`CONT-06` contrato, `ID-01` identidad y `IPC-01`…`IPC-03` comparabilidad.

## 6. Interfaz

- **Bandeja de revisión** (`/review`): carga de `.csv`/`.xlsx`/`.xls` con arrastrar
  y soltar, selectores accesibles de perfil y licencia, lista de contratos
  disponibles y **editor de reglas guiado**: un formulario genera el YAML y el
  motor lo valida campo a campo antes de guardarlo.
- **Detalle y gate** (`/review/[id]`): ficha, hallazgos filtrables por severidad,
  comparaciones con evidencia privada y formulario de gate con justificación de
  advertencias.
- **Consulta** (`/a/[id]`): ficha con fuente, base y periodo, tabla de series
  publicadas, reglas evaluadas, descarga de `recibo.json` y **ficha técnica
  imprimible** (`/a/[id]/ficha`) para adjuntar al ticket del procedimiento 18.
  No incluye comparador de periodos.

Estados: `borrador`, `no_habilitado`, `en_revision`,
`habilitado_para_consulta`, `cerrado`. No existe “aprobado por el INE”.

### Identidad visual

La interfaz implementa la *Guía de diseño gráfico para Datatón* (INE, noviembre
2026):

- **Logotipo.** Versiones vectoriales oficiales en `web/public/`: horizontal
  (`ine-logo-horizontal.svg`) en la cabecera; vertical
  (`ine-logo-vertical.svg`) en la ficha técnica; isologo (`ine-isologo.svg`)
  en el pie y el favicon. El isologo negativo
  (`ine-isologo-negative.svg`) se usa en blanco sobre azul oscuro en la
  portada. No hay efectos, recortes, recolores ni deformación.
- **Tonos principales.** Azul radiante `#0080FF`, azul oscuro `#004080` y
  blanco. La cinta superior retoma la secuencia azul / azul oscuro / naranja de
  la portada del manual.
- **Tonos secundarios.** Naranja `#FF5500`, verde lima `#9DD926`, lila
  `#A97EFF` y amarillo `#FFD500` para estados, acentos y fondos suaves.
- **Tipografía.** Ubuntu Sans variable, incluida en el kit y servida localmente
  desde `web/app/fonts/` (subconjunto latino en WOFF2, licencia UFL).
- **Fondos.** Blanco para tarjetas y superficies de contenido; gris claro
  `#F5F5F5` para el lienzo; el logotipo nunca se coloca sobre azul, fotografía
  o fondos con textura.

## 7. Servidor MCP (P1)

Componente opcional de solo lectura sobre `stores/public_snapshot/`. Sin LLM, sin
escritura y sin acceso a la cola de revisión.

| Herramienta | Devuelve |
|---|---|
| `list_enabled_aggregates()` | agregados con fuente, URL, fecha UTC, licencia, base, series y `decision_basis_digest` |
| `get_aggregate_receipt(case_id)` | metadatos del agregado y su recibo público (`technical_payload` y `decision_log`), o un bloqueo estructurado |

```json
{
  "mcpServers": {
    "ine-data-trust": {
      "command": "/ruta/a/ine-data-trust/.venv/bin/python",
      "args": ["/ruta/a/ine-data-trust/mcp/server.py"],
      "cwd": "/ruta/a/ine-data-trust"
    }
  }
}
```

```bash
pnpm run mcp
```

## 8. Pruebas

```bash
pnpm run test        # motor + tipos
```

- **Motor (pytest):** contrato, `.xls` heredado, identidad, comparabilidad,
  determinismo e invalidación del digest, gate, frontera de la API pública y
  aislamiento del MCP.
- **API HTTP:** recursos registrados, carga, gate, invalidación por cambio de contrato, recibos y creación de perfiles con
  errores de campo; el endpoint de comparación ya no existe.
- **Web:** `tsc --noEmit` sobre la interfaz.

## 9. Limitaciones

- No hay piloto en sombra ni prueba de usabilidad ejecutada.
- La habilitación corresponde a este sistema, no al INE. No hay firma
  criptográfica ni autenticación.
- `n<5` no se usa como garantía legal; no se afirma secreto estadístico.
- El hash prueba igualdad de bytes del par observado, no autoría ni calidad.
- La cobertura es la del perfil declarado, no la de toda la hoja.
- No hay comparador de periodos: el portal muestra metadatos, reglas y recibo, y
  no calcula variaciones entre periodos.
- El regional publica índices, no variaciones; el sistema no las calcula.
- La fecha de descarga del regional proviene de la mtime del archivo
  (`downloaded_at_source: "mtime"`), declarada en el manifiesto.

## 10. Licencias

- **Código:** MIT (`LICENSE`). No cubre los datos.
- **Datos INE:** `cc-by`, atribuidos al Instituto Nacional de Estadística (INE),
  Guatemala. La ficha y el manifiesto guardan licencia y fecha de descarga.
- **Dependencias:** `docs/LICENSES_THIRD_PARTY.md`, generado con
  `pnpm run licenses`.

## 11. IA, pagos y nube

- **IA en el producto:** ninguna. No hay modelos ni prompts en tiempo de
  ejecución; el motor es determinista y funciona sin red.
- **IA en el desarrollo:** ver `docs/AI_USAGE.md`.
- **Pagos:** ninguno.
- **Nube:** ninguna. Todo corre local; el único uso de red es la descarga inicial
  del snapshot y la instalación de dependencias.

## 12. Convención de idioma

Comentarios, docstrings e identificadores del código están en inglés. La
interfaz, los mensajes, los datos y esta documentación conservan el vocabulario
del PRD en español, que es el que lee el jurado y el que aparece en recibos,
decisiones y snapshot público.
