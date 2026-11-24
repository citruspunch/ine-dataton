# INE Data Trust · prototipo interactivo

Validación técnica de agregados oficiales ya publicados. El prototipo no calcula
cifras nuevas, no corrige archivos, no publica en CKAN y no certifica. Marca,
bloquea y deja un recibo reproducible para que una persona decida.

> **No implica certificación, aprobación ni adopción por el INE.**
> Datatón INE 2026, Categoría 2. Estado: prototipo funcional.

---

## 1. Problema y usuarios

Un agregado candidato puede parecer correcto y no ser comparable con su versión
oficial por **base, periodo, unidad, esquema, identidad o licencia**.

- **Usuario primario:** técnico de publicaciones que revisa un agregado al lado de
  la ficha oficial, dentro del flujo del **procedimiento 18** del Manual de
  procesos de la Dirección de Informática del INE (recepción, verificación de
  formato y publicación).
- **Usuario secundario:** periodista o analista que necesita fuente, base y
  periodo, y una negativa clara cuando pide comparar cosas que no se comparan.

El producto entrega **estado, severidad, cobertura y recibo**. No entrega un
puntaje de 0 a 100.

## 2. Qué hace y qué no hace

| Hace | No hace |
|---|---|
| Valida contrato, tipos, grano, periodo, unidad y base | No corrige ni reescribe el archivo |
| Detecta duplicados por SHA-256 e identidad semántica | No calcula un empalme propio |
| Bloquea comparaciones entre bases distintas | No muestra el número de una comparación inválida |
| Exige gate humano antes de publicar | No publica en CKAN |
| Exporta recibo JSON y ficha imprimible | No emite certificados ni scores |
| Expone dos herramientas MCP de solo lectura | No procesa microdatos ni PII |

Estados posibles: `borrador`, `no_habilitado`, `en_revision`,
`habilitado_para_consulta`, `cerrado`. **No existe “aprobado por el INE”.**

## 3. Arranque en un comando

Requisitos: Python 3.11 o superior.

```bash
make demo
```

Eso instala dependencias, prepara el snapshot sin red, valida los nueve casos,
registra el gate de cuatro agregados y arranca la interfaz en
**http://127.0.0.1:8000**.

Otros comandos:

```bash
make seed      # solo datos y decisiones (sin servidor)
make serve     # solo la interfaz
make test      # pytest: 80 pruebas
make mcp       # servidor MCP por stdio
make verify    # recalcula digests y retira agregados insostenibles
```

Manual equivalente:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python tools/prepare_snapshot.py --offline   # o sin --offline la 1.ª vez
.venv/bin/python tools/run_demo.py --reset
.venv/bin/python app.py
```

Todo funciona **sin red** después de preparar el snapshot. El motor (`idt/`) no
importa `urllib`, `requests` ni `socket`; hay un test que lo verifica.

## 4. Recorrido de la demo (7 minutos)

1. **0:00 · El bloqueo.** Portal de consulta → IPC → comparador. Serie F,
   `2024-12` vs `2025-01` → **+0,50 %**, variación publicada en `G504`.
2. **0:50 · El cruce inválido.** Cambiar Serie A a *E (base dic-2023)* →
   **bloqueada**, sin ningún número calculado. Regla `IPC-01`.
3. **1:40 · Bandeja de revisión.** Nueve casos, estados visibles. Abrir
   `csv_grano_duplicado` → `CONT-04` en falla, gate bloqueado.
4. **2:30 · Carga en vivo.** Subir cualquier `.csv`/`.xlsx`/`.xls`, elegir perfil y
   licencia → SHA-256 calculado y hallazgos por regla.
5. **3:30 · Identidad.** `dup_identidad` (mismos bytes, etiquetas distintas) en
   falla; `dup_identidad_excepcion` en advertencia justificada.
6. **4:30 · Gate humano.** Escribir responsable y motivo, aprobar → aparece en el
   portal de consulta con recibo.
7. **5:30 · Invalidación.** “Simular cambio en el perfil” → el digest cambia, la
   decisión se invalida y el agregado **desaparece** del portal.
8. **6:30 · Cierre.** Ficha imprimible + recibo JSON. Qué pedimos: piloto en
   sombra con un revisor de publicaciones.

## 5. Datasets reales utilizados

Ambos vienen del mismo conjunto CKAN del INE, **IPC Base Anual 2024=100**
(`dataset_id 4243818d-b479-4bc1-aae6-2735e2b51265`), licencia declarada `cc-by`.

| Recurso | Archivo | URL oficial | Descarga (UTC) | Bytes | SHA-256 |
|---|---|---|---|---|---|
| Empalme del IPC por República | `data/ipc_emprepu_es25.xlsx` | `…/resource/6b2cb40a-188c-47c9-9288-ba11c40b5910/download/ipc_emprepu_es25.xlsx` | 2026-11-24T05:41:54Z | 68.016 | `d0101e366ee6d6bb02345db64b8c725c0a4c65ee85aa800d751d41b8381664d4` |
| IPC por Región | `data/ipc_porreg_es25.xlsx` | `…/resource/04f7ee06-d597-4309-9522-c70e23e00e75/download/ipc_porreg_es25.xlsx` | 2026-11-24T19:34:21Z | 12.703 | `841dada98d20bca5ec8c23755ac8d793ce76b2e06dc7c82d34fc4f48475c8c1e` |

Las URL completas están en `data/sources.json` y en `data/manifest.json`; la ficha
de cada agregado las muestra en pantalla.

**Por qué el empalme.** Permite demostrar un error metodológico real y verificable:

| Celda | Valor | Qué es |
|---|---|---|
| `E503` | 101,702855 | índice base diciembre 2023=100 |
| `F503` | 100,513541 | índice base 2024=100 |
| `F504` | 101,017579 | índice base 2024=100 |
| `G504` | 0,501463 % | variación mensual **publicada** |

- `F504 / F503` es válido: misma base, meses contiguos → **+0,501463 %**, que
  coincide con la variación publicada en `G504`. La ficha muestra la cifra
  publicada, no una calculada.
- `F504 / E503` es **inválido**: mezcla bases. Da `−0,673802 %`. Ese número solo
  aparece en la pantalla privada de revisión: **no entra** al snapshot público,
  ni al export, ni a la ficha. Hay tests que lo verifican.

**Por qué el regional.** Es un segundo recurso real con **otra forma**: tabla
ancha (una columna por región), hoja `Hoja1`, sin columna de variación publicada y
con un rango de periodos (2025-01 a 2026-10). Se evalúa y publica **sin tocar el
motor** (FR-13).

Todo lo demás son **fixtures sintéticos** generados por
`tools/prepare_snapshot.py`, rotulados como tales en el manifiesto, en la ficha y
en la interfaz. No hay microdatos, PII ni datos de personas u hogares.

### Los nueve casos precargados

| Caso | Qué demuestra | Estado esperado |
|---|---|---|
| `ipc_empalme` | recurso real, comparabilidad, bloqueo entre bases | habilitado |
| `ipc_regional` | segundo perfil real, tabla ancha, rango de periodos | habilitado |
| `csv_ok` | contrato sintético correcto | habilitado |
| `csv_columna_faltante` | falta `unidad` → falla crítica | no habilitado |
| `csv_grano_duplicado` | `(año, mes, indicador)` repetido | no habilitado |
| `xlsx_ok` | mismo contrato en XLSX | en revisión |
| `xlsx_hoja_inesperada` | hoja `Resumen` ≠ `Datos` | no habilitado |
| `dup_identidad` | mismos bytes, etiquetas distintas | no habilitado |
| `dup_identidad_excepcion` | con política documentada | habilitado |

## 6. Arquitectura

```
review_store/                       public_snapshot/
  cases.json      lista cerrada        index.json
  fixtures/       sintéticos           aggregates/<caso>.json
  uploads/        archivos cargados    receipts/<caso>.json
  receipts/       recibos privados     (solo habilitados)
  decisions/      bitácora
  overrides/      simulación
  quarantine/     retirados
        \____________________________/
                 gate humano
```

- **Aislamiento estructural.** `idt/public_api.py` es la única puerta del portal y
  del MCP; solo abre rutas dentro de `public_snapshot/` y rechaza cualquier ruta
  que salga de ahí (`acceso_denegado`). El sitio público no contiene evidencia
  privada: hay tests que recorren todos los JSON publicados.
- **Gate humano.** Exige: ninguna regla crítica en `falla` o `no_evaluado`,
  licencia verificada, y toda advertencia justificada con dueño, motivo y fecha.
  Una advertencia justificada sobre una regla crítica puede pasar: es el camino de
  la excepción documentada de `ID-01`.
- **Digest reproducible.**

```
validation_digest = SHA-256(canonical(
    sha256 de archivos + digest(perfil) + digest(reglas) + hallazgos
))
```

  `decision_basis_digest` usa el mismo valor. No incluye timestamps de ejecución
  ni de decisión, ni la fecha de descarga. Dos ejecuciones dan el mismo digest; un
  cambio de archivo, perfil, reglas o hallazgo lo cambia y **invalida la decisión**.
- **Cierre por defecto.** `idt verify` retira del portal público cualquier agregado
  cuya decisión ya no sostenga el digest actual y lo mueve a `review_store/quarantine/`.
  Para republicarlo hace falta un nuevo gate.

## 7. Perfiles declarativos y reglas

Los perfiles son YAML editables (`profiles/*.yaml`) y **no declaran coordenadas**:

```yaml
period:
  year_column: year
  month_column: month
  expected: ["2024-12", "2025-01"]

comparisons:
  - id: mensual_ene_2025
    numerator:   { column: f_index, period: "2025-01" }
    denominator: { column: f_index, period: "2024-12" }
    published:   { column: g_monthly, period: "2025-01" }
    tolerance_pp: 0.005
```

Las columnas se resuelven por **encabezado** y los periodos por **año y mes**. Las
celdas (`F504`, `G504`) se descubren al leer el archivo y aparecen solo como
metadato informativo en la evidencia. Un test recorre los YAML y falla si alguien
vuelve a escribir `letter`, `row` o `cell`.

Reglas versionadas en `rules/rules.json` (`1.0.0`): `SNAP-01` integridad,
`LIC-01` licencia, `CONT-01`…`CONT-06` contrato, `ID-01` identidad y `IPC-01`…`IPC-03`
comparabilidad. Añadir un perfil no toca el motor.

## 8. Servidor MCP (P1)

Dos herramientas tipadas, deterministicas, de **solo lectura** sobre
`public_snapshot/`. Sin LLM dentro del servidor, sin escritura, sin acceso a
`review_store/`.

| Herramienta | Devuelve |
|---|---|
| `listar_agregados_habilitados()` | agregados con fuente, URL, fecha UTC, licencia, base, series y `decision_basis_digest` |
| `consultar_serie_ipc(periodo_inicio, periodo_fin)` | puntos del IPC con la variación **publicada**; bloqueo estructurado si el rango cruza bases o sale del snapshot |

Configuración para Claude Desktop (o cualquier cliente MCP local). Reemplace
`/ruta/a/ine-dataton` por la ruta real del repositorio:

```json
{
  "mcpServers": {
    "ine-data-trust": {
      "command": "/ruta/a/ine-dataton/.venv/bin/python",
      "args": ["/ruta/a/ine-dataton/mcp_server.py"],
      "cwd": "/ruta/a/ine-dataton"
    }
  }
}
```

Prueba rápida por stdio:

```bash
make mcp     # queda escuchando en stdio
```

## 9. Pruebas

```bash
make test
```

80 pruebas con `pytest`, sin servicios externos. Cubren:

- **Contrato:** caso positivo, columna faltante, grano duplicado, hoja inesperada,
  archivo ilegible, `.xls` heredado y ausencia de coordenadas en los perfiles.
- **Identidad:** mismos bytes con identidad incompatible y excepción documentada.
- **IPC:** par válido, cruce entre bases bloqueado, ausencia del número inválido en
  la evidencia pública, comparador del portal y consulta MCP.
- **Digest y gate:** determinismo, cambio por perfil, exclusión de timestamps,
  rechazo de fallas, aprobación con excepción, rechazo sin publicación.
- **Invalidación:** la simulación cambia el digest, retira el agregado y su
  reversión lo restaura.
- **Web:** bandeja, detalle, gate, carga en vivo, comparador, ficha y descargas.
- **MCP:** dos herramientas, bloqueos estructurados y aislamiento del almacén
  privado.

## 10. Estructura

```
app.py                 arranque de la interfaz web
mcp_server.py          servidor MCP por stdio
idt/
  engine.py            motor de reglas y digest
  gate.py              gate humano, decisiones, snapshot público
  public_api.py        puerta de solo lectura (portal y MCP)
  store.py             registro de archivos cargados
  config.py            perfiles YAML, manifiesto, rutas y decisiones
  web/                 FastAPI + Jinja2 (plantillas y CSS)
data/                  lista cerrada, manifiesto y los dos XLSX reales
profiles/              perfiles declarativos (YAML)
rules/                 reglas versionadas
review_store/          casos, fixtures, cargas, recibos, decisiones
public_snapshot/       agregados habilitados y recibos públicos
tests/                 pytest
tools/                 preparación, demo y licencias
```

## 11. Limitaciones

- **No hay piloto en sombra ni prueba de usabilidad ejecutada.** No se reportan
  resultados que no se midieron.
- La habilitación es del prototipo. No hay firma criptográfica ni autenticación: el
  visto bueno es una constancia local con responsable y motivo.
- `n<5` no se usa como garantía legal. No se afirma que el prototipo garantice
  secreto estadístico: los subtotales y distintos cortes permiten inferencias.
- El hash prueba igualdad de bytes del par observado. No prueba autoría, origen,
  licencia, causalidad ni calidad.
- El caso de duplicados usa un fixture sintético. El par real de divorcios y
  matrimonios es microdato y no se muestra.
- La cobertura es la del perfil declarado: 5 columnas del empalme, 11 del regional,
  no las 9 o 22 de cada hoja.
- **`.xls` heredado**: se lee con `xlrd` y se valida igual que un `.xlsx`, pero
  solo se extraen valores de la primera fila de datos en adelante; estilos,
  fórmulas y formato no se interpretan.
- El comparador público solo opera sobre los periodos publicados en el snapshot
  (2 en el empalme, 22 en el regional), no sobre la serie histórica completa.
- El regional publica **índices**, no variaciones: el comparador lo dice y no
  calcula una variación que el INE no publicó.
- La fecha de descarga del archivo regional proviene de la mtime del archivo
  (`downloaded_at_source: "mtime"` en el manifiesto), no de un registro de
  descarga, porque se incorporó al repositorio antes de que el manifiesto
  guardara ese campo.

## 12. Licencias

- **Código:** MIT (`LICENSE`). Esa licencia no cubre los datos.
- **Datos INE:** `cc-by`. Se atribuye al Instituto Nacional de Estadística (INE),
  Guatemala. El manifiesto y cada ficha guardan la licencia y la fecha de descarga.
- **Fixtures:** generados por el equipo, sin licencia de terceros.
- **Dependencias:** ver `LICENSES_THIRD_PARTY.md`, generado con
  `tools/gen_licenses.py` a partir de los metadatos instalados.
- Sin licencia verificada, el recurso **se cierra por defecto**: no se asume
  redistribución.

## 13. IA, pagos y nube

- **IA en el producto:** ninguna. No hay modelos, prompts ni servicios de IA en
  tiempo de ejecución; el motor es determinista y funciona sin red.
- **IA en el desarrollo:** se usaron asistentes de código (OpenCode con modelos
  DeepSeek y otros) para escribir y revisar código, pruebas y documentación. Todo
  resultado se verificó contra los archivos oficiales y la suite de pruebas.
- **Pagos:** ninguno.
- **Nube:** ninguna. Todo corre local; el único uso de red es la descarga inicial
  del snapshot.

## 14. Repositorio y elegibilidad

Repositorio nuevo creado para la Datatón. El historial de Git es la evidencia del
desarrollo durante el evento; no se reescribe ni se importa trabajo previo. La
carpeta de descubrimiento de datos (`discovery_ine/`) está en `.gitignore` porque
no forma parte de la entrega.
