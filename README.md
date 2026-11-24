# INE Data Trust · prototipo

Validación técnica de agregados oficiales ya publicados. El prototipo no calcula
cifras nuevas, no corrige, no publica en CKAN y no certifica. Marca, bloquea y
deja un recibo reproducible para que una persona decida.

> **No implica certificación, aprobación ni adopción por el INE.**
> Estado: primera simulación funcional, 23 y 24 de noviembre de 2026.

---

## 1. Qué dataset se usa y por qué

El único dataset real es el **XLSX oficial de empalme del IPC por República** del
INE de Guatemala:

```
data/ipc_emprepu_es25.xlsx
https://datos.ine.gob.gt/dataset/4243818d-b479-4bc1-aae6-2735e2b51265/resource/6b2cb40a-188c-47c9-9288-ba11c40b5910/download/ipc_emprepu_es25.xlsx
68.016 bytes · SHA-256 d0101e366ee6d6bb02345db64b8c725c0a4c65ee85aa800d751d41b8381664d4
Licencia declarada en CKAN: cc-by · descargado 2026-11-24T05:41:54Z (UTC)
```

Hoja `Hoja2`, 524 filas de datos, una fila por mes desde marzo de 1983. El caso
usable son las filas **503 y 504** (diciembre 2024 y enero 2025):

| Celda | Valor | Qué es |
|---|---|---|
| `E503` | 101,702855111367 | índice base diciembre 2023=100 |
| `F503` | 100,513540673814 | índice base 2024=100 |
| `F504` | 101,017579223309 | índice base 2024=100 |
| `G504` | 0,5014633313243735 % | variación mensual **publicada** |

**Por qué este dataset y no otro.** Permite demostrar el producto con un error
metodológico real y verificable, no inventado:

- `F504 / F503` es válido: misma serie, misma base, meses contiguos. Da
  `+0,501463 %`, que coincide con la variación publicada en `G504`. El prototipo
  **muestra la cifra publicada**, no la usa como función de difusión.
- `F504 / E503` es **inválido**: mezcla base 2024=100 con base diciembre 2023=100.
  Da `−0,673802 %`. La regla lo bloquea y ese número **solo** aparece en la
  pantalla privada de revisión: no entra al snapshot público, ni al export, ni a
  la ficha.

Los otros datasets del descubrimiento (`Canasta Viva`, `DINESE`, `+21`, `HBA`)
quedaron fuera por riesgo de interpretación, no por falta de atractivo visual: son
simulaciones o cambios de conteo que se leen como otra cosa. Ver PRD §4.

Todo lo demás son **fixtures sintéticos** generados por
`tools/prepare_snapshot.py`, rotulados como tales en el manifiesto, en la ficha y
en el sitio. No hay microdatos, ni PII, ni datos de personas, hogares o empresas.

---

## 2. Qué hace

Ocho casos de una **lista cerrada**. No hay URL libre, SQL, carga de archivos ni
agregación libre.

| Caso | Qué demuestra | Estado esperado |
|---|---|---|
| `ipc_empalme` | contrato XLSX real, grano, periodo, base, comparabilidad | habilitado |
| `csv_ok` | contrato CSV correcto | habilitado |
| `csv_columna_faltante` | falta `unidad` → falla crítica | no habilitado |
| `csv_grano_duplicado` | `(año, mes, indicador)` repetido → falla | no habilitado |
| `xlsx_ok` | segundo perfil declarativo, mismo motor | en revisión |
| `xlsx_hoja_inesperada` | hoja `Resumen` ≠ `Datos` → falla con `expected_sheet` y `observed_sheets` | no habilitado |
| `dup_identidad` | mismos bytes, etiquetas distintas → falla | no habilitado |
| `dup_identidad_excepcion` | misma duplicación con política documentada → advertencia justificada | habilitado |

Reglas (`rules/rules.json`, versión `1.0.0`): `SNAP-01` integridad de bytes,
`LIC-01` licencia verificada, `CONT-01` a `CONT-06` contrato, `ID-01` identidad
por SHA-256 y `IPC-01` a `IPC-03` comparabilidad.

### Lo que el prototipo no hace

No certifica, no corrige, no publica en CKAN, no procesa microdatos, no ofrece SQL
ni URL libre, no produce un score de 0 a 100, no es un chatbot, no es un monitor y
no promete tiempos de respuesta. No existe el estado "aprobado por el INE".

---

## 3. Arquitectura

```
review_store/                     public_snapshot/
  cases.json      lista cerrada      index.json
  fixtures/        sintéticos        aggregates/<caso>.json   solo habilitados
  receipts/        recibos privados  site/                    ficha de consulta
  decisions/       bitácora
  site/            revisión privada
        \__________________________/
                 gate humano
```

- `review_store/` es local y privado: candidatos, fixtures, recibos y decisiones.
- `public_snapshot/` solo recibe agregados habilitados después del visto bueno.
- El sitio público **solo** lee `public_snapshot/`. Los tests verifican que el
  snapshot no contenga evidencia privada ni la ruta de revisión.
- Sin red después de preparar el snapshot. `idt/` no importa `urllib`, `requests`
  ni `socket`; hay un test que lo comprueba.

### Estados

| Estado | Condición | Texto visible |
|---|---|---|
| `borrador` | snapshot o ficha incompletos | Borrador, no consultable |
| `no_habilitado` | falla crítica o crítica no evaluada | No habilitado para consulta |
| `en_revision` | sin fallas críticas; advertencias o gate pendiente | En revisión |
| `habilitado_para_consulta` | críticas sin falla, licencia y gate | Habilitado para consulta en el prototipo |
| `cerrado` | licencia o permiso insuficiente | Cerrado por defecto |

No es un puntaje: se muestran estado, severidad y cobertura
(`critical_evaluated / critical_total`).

### Gate humano y digest

El gate exige: ninguna regla crítica en `falla` o `no_evaluado`, licencia
verificada, y **toda advertencia justificada** con política, dueño, fecha y motivo
(`review_store/justifications.json`). Una advertencia justificada sobre una regla
crítica puede pasar — es el camino de la excepción documentada de `ID-01`.

El digest es reproducible y no incluye timestamps:

```
validation_digest = SHA-256(canonical(
    sha256 de archivos + digest(perfil) + digest(reglas) + hallazgos
))
```

`decision_basis_digest` usa el mismo valor. Si cambia un archivo, el perfil, la
versión de reglas o un hallazgo, el digest cambia y la decisión queda invalidada.
`idt verify` lo informa y **retira el agregado del snapshot público**, moviéndolo a
`review_store/quarantine/` con el motivo: un agregado sin decisión vigente no se
sirve. Volver a habilitarlo exige un nuevo `promote`. Los timestamps de ejecución y
de decisión viven en el recibo y en la bitácora, fuera del digest. La fecha de
descarga tampoco entra al digest: un nuevo snapshot con los mismos bytes no
invalida una decisión.

---

## 4. Instalación y uso

Requisitos: Python 3.11 o superior. Dependencia única: `openpyxl`.

```bash
make setup            # crea .venv e instala requirements.txt
make demo             # prepara offline, valida, habilita 3 casos, genera sitios
make test             # 33 tests
```

Manual:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

.venv/bin/python tools/prepare_snapshot.py            # primera vez: descarga
.venv/bin/python tools/prepare_snapshot.py --offline  # sin red

.venv/bin/python -m idt list
.venv/bin/python -m idt validate ipc_empalme
.venv/bin/python -m idt validate --summary
.venv/bin/python -m idt promote ipc_empalme \
    --operator "Técnico de publicaciones" \
    --rationale "Ficha oficial cotejada contra G504."
.venv/bin/python -m idt export ipc_empalme
.venv/bin/python -m idt site
.venv/bin/python -m idt verify
```

Sitios generados (abrir con el navegador, funcionan sin red):

- `public_snapshot/site/index.html` — ficha de consulta.
- `review_store/site/index.html` — pantalla privada de revisión, con la evidencia
  privada de las comparaciones bloqueadas.

---

## 5. Estructura del repositorio

```
idt/                 motor: lector, reglas, estados, gate, recibos, sitios, CLI
  canonical.py       JSON canónico y SHA-256
  reader.py          CSV y XLSX de una hoja
  engine.py          reglas y digest
  gate.py            precondiciones, decisiones, snapshot público
  site.py            dos superficies estáticas
data/
  sources.json       lista cerrada (URLs, licencias, perfiles)
  manifest.json      generado: bytes, SHA-256, fecha UTC
  ipc_emprepu_es25.xlsx
profiles/            perfiles declarativos (IPC, contrato CSV, contrato XLSX, par)
rules/rules.json     reglas versionadas
review_store/        casos, fixtures, recibos, decisiones, sitio privado
public_snapshot/     agregados habilitados y ficha de consulta
tests/               unittest, sin dependencias externas
tools/               prepare_snapshot.py y run_demo.py
```

---

## 6. Limitaciones declaradas

- **No hay piloto en sombra ni prueba de usabilidad ejecutada.** No se reportan
  resultados que no se midieron.
- La habilitación es del prototipo. No hay firma criptográfica ni autenticación:
  el visto bueno es una constancia local con responsable y motivo.
- `n<5` no se usa como garantía legal. No se afirma que el prototipo garantice
  secreto estadístico: los subtotales y distintos cortes permiten inferencias.
- El hash prueba igualdad de bytes del par observado. No prueba autoría, origen,
  licencia, causalidad ni calidad.
- El caso de duplicados usa un fixture sintético. El par real de divorcios y
  matrimonios es microdato y no se muestra.
- La cobertura es la del perfil declarado: 5 columnas del IPC, no las 9 de la
  hoja. `CONT-01` no aplica a CSV.
- No se implementó MCP (P1): la decisión del PRD dependía de tener las P0 verdes
  y tiempo, y no es requisito de entrega.
- El XLSX se lee con `openpyxl` en modo `data_only`; si el archivo trae fórmulas
  sin caché, el valor no está disponible y la regla lo reporta.

---

## 7. Licencias

- **Código:** MIT, ver `LICENSE`. Esa licencia no cubre los datos.
- **Datos INE:** el XLSX conserva su licencia `cc-by`; se atribuye al Instituto
  Nacional de Estadística (INE), Guatemala. El manifiesto guarda la evidencia de
  la licencia y la fecha de descarga.
- **Fixtures:** generados por el equipo, sin licencia de terceros.
- Sin licencia verificada, el recurso se cierra por defecto: no se asume
  redistribución.

## 8. IA, pagos y nube

- **IA:** no hay modelos, prompts ni servicios de IA en el producto; el motor es
  determinista y funciona sin red. Estas herramientas de asistencia se usaron
  para escribir código y documentación, y el resultado se verificó contra el
  archivo oficial.
- **Pagos:** ninguno.
- **Nube:** ninguna. Todo corre local; el único uso de red es la descarga inicial
  del snapshot.

## 9. Repositorio y elegibilidad

Repositorio nuevo creado para la Datatón. El historial de Git es la evidencia del
desarrollo durante el evento; no se reescribe ni se importa trabajo previo. El
descubrimiento de datos (carpeta `discovery_ine/`) está en `.gitignore` porque no
forma parte de la entrega.
