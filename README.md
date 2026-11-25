# Monitor de presión de servicios y crecimiento local

Comparador municipal para Guatemala que cruza las proyecciones de población y los
hechos vitales de 2025 del INE con los registros de establecimientos y estudiantes
del MINEDUC y con la pobreza municipal y la asignación constitucional de SEGEPLAN.

> **Herramienta independiente.** No es un sistema oficial del INE ni un producto
> interinstitucional. Las comparaciones son descriptivas y no implican causalidad.
> Los datos de SEGEPLAN están bajo **CC BY-NC 2.0: uso no comercial únicamente**.

La interfaz está en español porque está pensada para equipos municipales y de
planificación local en Guatemala. El código, los comentarios y este README están
en inglés/español según el contexto.

---

## 1. Problema y usuarios

Los municipios de Guatemala reciben señales de demanda —nacimientos, crecimiento
poblacional proyectado, presión sobre la oferta escolar— y, al mismo tiempo,
decisiones de asignación de recursos que no siempre se leen juntas. Los códigos
municipales llegan en formatos distintos según la institución, los conjuntos
tienen licencias diferentes y los conteos pequeños están protegidos por el secreto
estadístico.

Esta aplicación resuelve tres problemas prácticos:

1. **Unir los datos sin perder municipios.** Normaliza códigos de 2 y 4 dígitos,
   aplica el cruce +21 de los 16 municipios del departamento de Guatemala y
   verifica que las 340 filas municipales sobrevivan a todos los cruces.
2. **Comparar presión relativa.** Ofrece tres indicadores seleccionables y una
   tabla ordenable con los 340 municipios, no solo con los casos grandes.
3. **Hacer visible la procedencia y los límites.** Cada indicador muestra su
   fuente, fecha UTC de descarga, SHA-256, licencia y la regla de supresión
   aplicada.

**Usuarios principales**

- Equipos municipales de planificación y desarrollo local que comparan municipios
  dentro de un departamento.
- Analistas de política pública que necesitan una lectura reproducible y
  documentada de las fuentes, con sus licencias y limitaciones.
- Jurados y equipos técnicos que deben poder ejecutar la herramienta localmente
  sin servicios en la nube ni llaves de acceso.

---

## 2. Qué hace la aplicación

### 2.1 Indicadores seleccionables

| Indicador | Fórmula | Dirección de presión | Fuentes |
|---|---|---|---|
| Crecimiento poblacional 2025–2035 | `(población_2035 − población_2025) / población_2025 × 100` | Mayor valor = más presión | INE, proyecciones municipales 2015–2035 y 2015–2030 |
| Nacimientos por escuela (2025 / 2022) | `nacimientos_2025 / escuelas_2022` | Mayor valor = más presión | INE nacimientos 2025 + MINEDUC establecimientos 2022 |
| Presión de la asignación constitucional 2026 | `(asignación nacional / población nacional) / (asignación municipal / población municipal)`, con la población usada por SEGEPLAN en el cálculo | Mayor valor = menos recursos por residente | SEGEPLAN asignación 2026 |

Los tres indicadores se convierten en **percentiles relativos** entre los 340
municipios para las clases `Presión alta` (≥ 75), `Presión media-alta` (≥ 50),
`Presión media` (≥ 25) y `Presión baja` (< 25). No son umbrales oficiales del INE
ni una calificación de desempeño municipal.

### 2.2 Indicadores de contexto

La tabla y la ficha de fuentes también incluyen:

- Población 2015, 2025, 2030 y 2035.
- Nacimientos y defunciones de residentes en 2025, y defunciones de menores de 5
  años.
- Establecimientos educativos y estudiantes matriculados en 2022, incluidos los
  del sector oficial.
- Pobreza general y extrema 2023, brecha, severidad y consumo promedio.
- Asignación constitucional 2026, asignación por habitante, ingresos propios per
  cápita y número de aldeas y caseríos.
- Tasas derivadas: nacimientos por 1,000 habitantes, mortalidad general,
  mortalidad de menores de 5 años, nacimientos por 100 estudiantes, estudiantes
  por escuela, escuelas y estudiantes por 10,000 habitantes.

### 2.3 Experiencia de uso

- **Controles superiores:** selector de departamento, selector de indicador y
  búsqueda de municipio.
- **Resumen del departamento:** tres cifras —población 2025, crecimiento
  2025–2035 y municipios en presión alta— que se recalculan con el indicador
  seleccionado.
- **Ranking de presión:** los 10 municipios con mayor presión del departamento
  seleccionado, o el top 10 nacional si se elige "Todos los departamentos". En
  móvil se muestra como lista compacta con barras proporcionales.
- **Tabla municipal:** sigue al departamento seleccionado por defecto, con
  paginación, ordenamiento y acceso a "Ver los 340". En móvil se convierte en
  tarjetas legibles. Al hacer clic en una fila se abre una ficha con el perfil
  completo del municipio.
- **Ficha municipal:** los tres indicadores de presión, población y hechos
  vitales, servicios educativos, pobreza y recursos, y las celdas suprimidas.
- **Pestaña "Datos y fuentes":** licencias destacadas, lista expandible de
  archivos con URL, fecha UTC, SHA-256 y estado, reglas de supresión, calidad de
  los cruces, limitaciones y declaración de uso de IA.

---

## 3. Arquitectura y stack

```text
INE / MINEDUC / SEGEPLAN
        │  URLs exactas en pipeline/sources.py
        ▼
pipeline/download.py  ── cache local + data/manifest.json (URL, UTC, SHA-256)
        ▼
pipeline/normalize.py ── códigos de 4 dígitos + cruce +21 de Guatemala
        ▼
pipeline/projections.py / vital.py / education.py / segeplan.py
        ▼
pipeline/indicators.py ── cruces 340/340 + fórmulas + percentiles
        ▼
pipeline/suppression.py ── supresión de conteos 1–4 y tasas derivadas
        ▼
data/processed/*.parquet + indicators.json + provenance.json
        ▼
web/ (Next.js + TypeScript + Tailwind + shadcn/ui + Recharts)
```

### Stack

| Capa | Tecnología | Gestión |
|---|---|---|
| Pipeline | Python 3.12, pandas, openpyxl, pyarrow, requests, truststore | `uv`, `pyproject.toml`, `uv.lock` |
| Pruebas | pytest | `uv run pytest` |
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS 4 | `pnpm`, `web/package.json`, `web/pnpm-lock.yaml` |
| Componentes | shadcn/ui (Radix UI), lucide-react | `web/src/components/ui` |
| Gráfico | Recharts + `ChartContainer` de shadcn/ui | `web/src/components/indicator-chart.tsx` |
| Datos locales | Parquet + JSON estático en `web/public/data` | sin nube, sin llaves, sin base de datos |

### Estructura del repositorio

```text
local-growth-pressure-monitor/
├── pipeline/
│   ├── sources.py         Registro cerrado de URLs, licencias y atribuciones
│   ├── download.py        Cache, descarga atómica, manifiesto y SHA-256
│   ├── normalize.py       Códigos de 4 dígitos y cruce +21
│   ├── projections.py     Proyecciones 2015–2035 y 2015–2030; validación de traslape
│   ├── vital.py           Nacimientos y defunciones 2025 por residencia
│   ├── education.py       Establecimientos y estudiantes MINEDUC 2022
│   ├── segeplan.py        Pobreza 2023 y asignación constitucional 2026
│   ├── indicators.py      Cruces 340/340, fórmulas y percentiles
│   ├── suppression.py     Supresión de celdas pequeñas
│   └── build.py           CLI `build-pressure`
├── tests/                 pytest: unitarios + integración
├── data/
│   ├── manifest.json      Metadatos de los archivos crudos
│   ├── reference/         Catálogo de los 340 municipios
│   └── processed/         Parquet, JSON y manifiesto de procedencia
├── web/
│   ├── src/app/           Next.js App Router
│   ├── src/components/    UI, gráfico, tabla, fuentes
│   ├── src/components/ui/ Componentes shadcn/ui
│   ├── src/lib/           Tipos, formato y utilidades
│   └── public/data/       Copia estática de indicators.json y provenance.json
├── pyproject.toml
├── uv.lock
├── README.md
└── LICENSE
```

---

## 4. Instalación y ejecución

### Requisitos

- Python 3.12 o superior.
- `uv` instalado.
- Node.js 20 o superior y `pnpm` instalado.

### 4.1 Pipeline de datos

```bash
# Desde la raíz del proyecto
uv sync
uv run build-pressure
```

`build-pressure`:

1. Revisa `data/` y reutiliza los `.xlsx` y `.csv` que ya existan.
2. Descarga los que falten desde la URL exacta del registro.
3. Registra URL, fecha UTC, SHA-256, bytes y estado en `data/manifest.json`.
4. Normaliza, cruza, calcula indicadores y aplica supresión.
5. Escribe Parquet/JSON y `data/processed/provenance.json`.
6. Copia `indicators.json` y `provenance.json` a `web/public/data/`.

La primera ejecución descarga aproximadamente 87 MB. Las siguientes funcionan sin
red porque los archivos quedan cacheados en `data/`.

### 4.2 Frontend

```bash
cd web
pnpm install
pnpm dev
```

Abrir `http://localhost:3000`. Si el puerto está ocupado:

```bash
pnpm exec next dev -p 3010
```

Para una compilación de producción:

```bash
cd web
pnpm build
pnpm start
```

### 4.3 Pruebas y verificación

```bash
# Desde la raíz
uv run pytest

cd web
pnpm typecheck
pnpm build
```

Las pruebas de integración requieren los archivos crudos en `data/`; si faltan,
se omiten con un mensaje que indica ejecutar `uv run build-pressure`.

### 4.4 Ejecución sin red después de la primera descarga

```bash
uv run build-pressure --skip-download
```

Este modo falla de forma explícita si falta un archivo, en lugar de intentar
descargarlo. Sirve para demostraciones y auditorías offline.

---

## 5. Pipeline: decisiones de rigor

### 5.1 Registro cerrado de fuentes

Todas las URLs viven en `pipeline/sources.py`. La aplicación no descubre URLs en
tiempo de ejecución ni las construye a partir de datos de usuario. Cada fuente
tiene título, editor, página del conjunto, URL de descarga, formato, licencia,
atribución, descripción y tamaño mínimo esperado.

### 5.2 Cache y descarga

`pipeline/download.py`:

- No vuelve a descargar un archivo existente.
- Escribe en un archivo temporal y hace `os.replace` atómico.
- Valida el tamaño mínimo, la firma ZIP de los `.xlsx` y que los `.csv` no sean
  páginas HTML.
- Reintenta hasta 6 veces con espera exponencial ante errores transitorios.
- Usa `truststore` para confiar en el almacén de certificados del sistema
  operativo; el portal del MINEDUC presenta una cadena que no está en `certifi`.
- Escribe el manifiesto después de cada archivo, de modo que una falla posterior
  no borre la evidencia de las descargas ya completadas.

Los nombres locales llevan un prefijo institucional (`ine_`, `mineduc_`,
`segeplan_`) para evitar colisiones. El nombre original, la URL y el hash están
en `data/manifest.json` y en la pestaña "Fuentes y licencias".

### 5.3 Códigos municipales y cruce +21

- La tabla ancha 2015–2035 usa códigos como `101` y `2217`; se normalizan a
  `0101` y `2217`.
- La tabla larga 2015–2030 usa `0101` para la ciudad de Guatemala y
  `0123`–`0138` para los otros 16 municipios del departamento. El catálogo
  vigente usa `0102`–`0117`. El cruce resta 21 al correlativo municipal:
  `0123 → 0102`, …, `0138 → 0117`.
- Se valida que el cruce se aplique exactamente a 16 municipios y que no queden
  códigos `0123`–`0138` en la salida.
- La tabla larga contiene filas `SEXO=0` (total), `1` (hombres) y `2` (mujeres).
  El pipeline suma solo `SEXO=0`; sumar las tres duplicaría la población. Esta
  falla se detecta con la validación de traslape.

### 5.4 Validación de traslape

Las dos vigencias de proyección se comparan en los años 2015–2030. Para los 340
municipios, la diferencia absoluta máxima observada es **0 personas**. Si la
diferencia superara la tolerancia de 1 persona, el pipeline falla en lugar de
mezclar series incompatibles.

### 5.5 Hechos vitales

- Nacimientos: se agregan por `Deprem` + `Muprem` (residencia de la madre) y
  `Añoreg = 2025`.
- Defunciones: se agregan por `Dredif` + `MreDif` (residencia del fallecido) y
  `Añoreg = 2025`.
- Defunciones de menores de 5 años: `Edadif < 5`.
- Los códigos `2300` y `9999` —municipio desconocido o del exterior— se excluyen
  y se cuentan en el manifiesto. No se imputan a un municipio.
- En la descarga usada: 238,109 nacimientos y 88,181 defunciones asignados a los
  340 municipios; 10,088 y 3,662 registros excluidos respectivamente.

Los archivos crudos de nacimientos y defunciones son microdatos. Se excluyen de
Git, no se sirven desde la aplicación y no se redistribuyen; el repositorio y la
interfaz solo contienen agregados municipales. La herramienta no intenta
identificar personas, hogares ni empresas.

### 5.6 MINEDUC

- Se usa el ciclo 2022, el último publicado en el portal CKAN del MINEDUC.
- Establecimientos: conteo de `CodigoEst` únicos por municipio.
- Estudiantes: suma de `InscritosTotal` por municipio.
- Se calcula también el subconjunto del sector oficial.
- Los 340 códigos municipales están presentes.

### 5.7 SEGEPLAN

- Pobreza municipal 2023: archivo separado por punto y coma, codificación UTF-8
  con BOM. La pobreza extrema no está publicada para 23 municipios y se conserva
  como `null`, no como cero.
- Asignación constitucional 2026: archivo en Latin-1, montos como `Q160,927,138.93`.
  Se convierten a número y se calcula la asignación por habitante.
- Ambos conjuntos se publican con CKAN `cc-nc` (CC BY-NC 2.0).

### 5.8 Supresión estadística

- Regla: los conteos no nulos **1–4** se suprimen; los ceros se publican como
  cero.
- Las tasas derivadas se suprimen si cualquiera de sus componentes fue suprimido.
- En la corrida actual: 120 municipios con defunciones de menores de 5 años
  suprimidas, 1 municipio con una escuela pública suprimida y 120 tasas de
  mortalidad de menores de 5 años suprimidas. Total: **241 celdas**.
- En la interfaz, la celda muestra `— §` y la fila lleva la insignia `§ <5`.
- En Parquet/JSON, el valor es `null` y la bandera `*_suprimido` es `true`. El
  valor original no se exporta.
- Base legal citada: **Decreto-Ley 3-85, Ley de Estadística, y sus reglamentos**.
  El umbral 5 es una decisión conservadora del prototipo, no una marca oficial de
  supresión del INE.

---

## 6. Fuentes, descargas y licencias

Las fuentes se verificaron el **23 de noviembre de 2026**. Las descargas se
ejecutaron en la noche del 24 de noviembre de 2026 (hora local de Guatemala), que
en UTC corresponde al **25 de noviembre de 2026**. Los timestamps exactos están en
`data/manifest.json` y `data/processed/provenance.json`.

### 6.1 Archivos crudos

| ID | Archivo | URL exacta | Descarga UTC | Licencia / estado CKAN |
|---|---|---|---|---|
| `ine-proyecciones-2035` | `ine_proyecciones_municipales_2015_2035.xlsx` | `https://www.ine.gob.gt/ine/wp-content/uploads/2020/08/Estimaciones-y-Proyecciones-Municipales-2015-2035.xlsx` | `2026-11-25T04:43:45Z` | INE, página institucional; CKAN no declarado (`not_published_on_ckan`) |
| `ine-proyecciones-2030` | `ine_proyecciones_municipales_2015_2030.xlsx` | `https://datos.ine.gob.gt/dataset/23bbe8f8-ec9b-49c9-bcca-de78bec4efc0/resource/56b97bc0-5624-408d-a136-3931dd05610a/download/estimaciones-y-proyecciones-de-la-poblacion-total-por-municipio-segun-sexo-y-edad.-2015-2030.xlsx` | `2026-11-25T04:43:46Z` | ODC-BY (`odc-by`), declarada |
| `ine-nacimientos-2025` | `ine_nacimientos_2025.xlsx` | `https://datos.ine.gob.gt/dataset/96888fc0-5ced-4a58-bfd0-2a6a292e3208/resource/b6847c70-a0b9-4cfd-a405-4ea4360905d7/download/nacimientos_2025.xlsx` | `2026-11-25T04:48:49Z` | INE, CKAN sin licencia declarada (`not_declared`) |
| `ine-defunciones-2025` | `ine_defunciones_2025.xlsx` | `https://datos.ine.gob.gt/dataset/14f547c3-ad37-4ea1-9e74-16a3ed50ff54/resource/43adb351-0a14-4783-8401-e5ef21a2222e/download/defunciones_2025.xlsx` | `2026-11-25T04:49:53Z` | INE, CKAN sin licencia declarada (`not_declared`) |
| `mineduc-establecimientos-2022` | `mineduc_establecimientos_2021_2022.csv` | `https://datosabiertos.mineduc.gob.gt/dataset/6daf991d-59fc-4f2c-a64c-35759ee6cba0/resource/b7377ce0-0c66-4f8c-89d7-fd52fc7ab47b/download/establecimientos_2021-2022.csv` | `2026-11-25T04:51:11Z` | CC0 1.0 (`cc-zero`), declarada |
| `mineduc-estudiantes-2022` | `mineduc_estudiantes_2021_2022.csv` | `https://datosabiertos.mineduc.gob.gt/dataset/4d947596-0b42-4a9a-b151-53d74b230dd5/resource/3774793e-1c80-4b6a-a0d8-6dca91e51c0a/download/estudiantes_2021-2022.csv` | `2026-11-25T04:51:34Z` | CC0 1.0 (`cc-zero`), declarada |
| `segeplan-pobreza-2023` | `segeplan_pobreza_municipal_2023.csv` | `https://datos.segeplan.gob.gt/dataset/bfddf2e8-db9b-408f-b2b6-2519e207b150/resource/40ccb784-5f6d-47ab-8343-342fa2caabeb/download/datos-abiertos_resultados-mapa2023_mupio.csv` | `2026-11-25T04:51:48Z` | **CC BY-NC 2.0** (`cc-nc`), declarada; **no comercial** |
| `segeplan-asignacion-2026` | `segeplan_asignacion_constitucional_2026.csv` | `https://datos.segeplan.gob.gt/dataset/f4ee4102-b724-4617-8343-95a03e7fe34b/resource/8df77811-4e24-4fe8-af78-6e40153850f8/download/calculo-matematico-para-la-asignacion-constitucional-a-las-municipalidades-del-ano-2026.csv` | `2026-11-25T04:51:50Z` | **CC BY-NC 2.0** (`cc-nc`), declarada; **no comercial** |

El catálogo `data/reference/municipios_gt_340.csv` es derivado de la tabla
municipal 2015–2035 del INE, no una descarga separada.

### 6.2 SHA-256 de los archivos crudos

<details>
<summary>Ver hashes completos</summary>

| ID | SHA-256 | Bytes |
|---|---|---|
| `ine-proyecciones-2035` | `d2d1e1ab902571040806d9e8b4ad29db15b2b8b475c2f5fa97a057b5115ed4fb` | 68,367 |
| `ine-proyecciones-2030` | `b00fa494491b5b06e2fb7dac98df2441b6670e8d9a748cc97c2e72ed5012f499` | 7,775,292 |
| `ine-nacimientos-2025` | `12dd75c254f3c37e2637fb76ee6a5e1b11ffdfcec738f90e46a16605945b39e9` | 39,102,416 |
| `ine-defunciones-2025` | `332da4f661f78db0eab9788450fffaea68f4eedd22febac100790600c51870a7` | 8,918,540 |
| `mineduc-establecimientos-2022` | `8d8a2dd991ad8209e1fb3d4d159c361985bc9132e17c741087aa68c8baa6ebd3` | 20,672,969 |
| `mineduc-estudiantes-2022` | `c43f38ae61260636292b5fec3fc47e0a3f4fb18c5e50b0d13a2e07f92bebc206` | 12,772,841 |
| `segeplan-pobreza-2023` | `462e10c77aa9d5c5ad8e43250e0da1c24679161cde4be944cfd93f67127ab277` | 59,568 |
| `segeplan-asignacion-2026` | `c3f896c1ccfd26e20272809712cd3c69e5abf8f01b6166163d41129fb10f0af7` | 47,817 |

</details>

### 6.3 Licencias y atribución

- **MINEDUC:** Creative Commons CCZero (CC0 1.0). Se permite reutilización,
  incluida la comercial, sin atribución obligatoria; aun así se cita al MINEDUC.
- **SEGEPLAN:** Creative Commons Atribución-NoComercial 2.0 (CC BY-NC 2.0).
  Se permite compartir y adaptar con atribución, **solo para fines no
  comerciales**. Cualquier uso comercial requiere autorización expresa de
  SEGEPLAN. La aplicación muestra esta advertencia en la cabecera, en la pestaña
  de fuentes y en el pie de página.
- **INE 2015–2030:** Open Data Commons Attribution License (ODC-BY), declarada en
  CKAN. Reutilización permitida con atribución.
- **INE 2015–2035:** publicada en el sitio institucional del INE, no en el catálogo
  CKAN. No se atribuye una licencia abierta distinta de la que el INE declara; se
  cita la fuente y se recomienda verificar los términos vigentes.
- **INE nacimientos y defunciones 2025:** el recurso CKAN no tiene `license_id`.
  Se cita al INE y no se afirma una licencia abierta que no esté declarada.
- **Código de la aplicación:** MIT (ver `LICENSE`). Las dependencias conservan sus
  licencias originales.

Atribuciones sugeridas:

```text
Instituto Nacional de Estadística (INE), Guatemala. Estimaciones y proyecciones
de población municipal 2015–2035 y estadísticas vitales 2025.

Ministerio de Educación (MINEDUC), Guatemala. Establecimientos y estudiantes
2021–2022. Datos abiertos, CC0 1.0.

SEGEPLAN. Mapas de pobreza a nivel municipal 2023 y Cálculo matemático de la
asignación constitucional 2026. CC BY-NC 2.0, uso no comercial.
```

---

## 7. Diccionario de datos

| Campo | Descripción |
|---|---|
| `municipio_codigo` | Código municipal de 4 dígitos: 2 de departamento + 2 de municipio. |
| `municipio_nombre` | Nombre municipal del catálogo INE. |
| `departamento_codigo` | Código de departamento de 2 dígitos. |
| `departamento_nombre` | Nombre del departamento. |
| `poblacion_2015` | Población proyectada al 30 de junio de 2015. |
| `poblacion_2025` | Población proyectada al 30 de junio de 2025. |
| `poblacion_2030` | Población proyectada al 30 de junio de 2030 (serie 2015–2035). |
| `poblacion_2030_ckan` | Población 2030 de la serie larga 2015–2030, usada para validar el traslape. |
| `poblacion_2035` | Población proyectada al 30 de junio de 2035. |
| `crecimiento_abs_2025_2035` | Diferencia en personas entre 2035 y 2025. |
| `crecimiento_poblacional_pct` | Variación porcentual 2025–2035. |
| `crecimiento_poblacional_pct_2015_2025` | Variación porcentual 2015–2025. |
| `nacimientos_2025` | Nacimientos de residentes en 2025; suprimido si es 1–4. |
| `defunciones_2025` | Defunciones de residentes en 2025; suprimido si es 1–4. |
| `defunciones_menores_5_2025` | Defunciones de residentes menores de 5 años en 2025; suprimido si es 1–4. |
| `nacimientos_por_1000_habitantes_2025` | Nacimientos por 1,000 habitantes. |
| `tasa_mortalidad_general_2025` | Defunciones por 1,000 habitantes. |
| `tasa_mortalidad_menor_5_2025` | Defunciones de menores de 5 años por 1,000 nacimientos; suprimida si el conteo base es 1–4. |
| `relacion_nacimientos_defunciones_2025` | Nacimientos / defunciones. |
| `escuelas_2022` | Establecimientos educativos únicos en 2022. |
| `escuelas_publicas_2022` | Establecimientos del sector oficial en 2022. |
| `estudiantes_2022` | Matrícula total 2022. |
| `estudiantes_publicos_2022` | Matrícula del sector oficial 2022. |
| `nacimientos_por_escuela_2025` | Nacimientos 2025 / escuelas 2022. |
| `estudiantes_por_escuela_2022` | Estudiantes 2022 / escuelas 2022. |
| `nacimientos_por_100_estudiantes_2025` | Nacimientos 2025 / estudiantes 2022 × 100. |
| `escuelas_por_10000_habitantes_2022` | Escuelas 2022 / población 2025 × 10,000. |
| `estudiantes_por_10000_habitantes_2022` | Estudiantes 2022 / población 2025 × 10,000. |
| `pobreza_general_pct_2023` | Incidencia de pobreza general 2023. |
| `pobreza_extrema_pct_2023` | Incidencia de pobreza extrema 2023; `null` para 23 municipios. |
| `poblacion_en_pobreza_2023` | Personas en pobreza general 2023. |
| `poblacion_en_pobreza_extrema_2023` | Personas en pobreza extrema 2023; puede ser `null`. |
| `brecha_pobreza_general_2023` | Brecha FGT1. |
| `severidad_pobreza_general_2023` | Severidad FGT2. |
| `consumo_promedio_q_mes_2023` | Consumo promedio per cápita en quetzales por mes (oct. 2023). |
| `asignacion_constitucional_2026_gtq` | Situado constitucional 2026 en quetzales. |
| `poblacion_asignacion_2025` | Población usada por SEGEPLAN en el cálculo 2026. |
| `asignacion_por_habitante_2026_gtq` | Asignación 2026 / población de cálculo. |
| `asignacion_presion_indice_2026` | Promedio nacional por habitante / asignación municipal por habitante. |
| `ingresos_propios_2024_gtq` | Ingresos propios municipales 2024. |
| `ingresos_propios_per_capita_2024_gtq` | Ingresos propios por habitante 2024. |
| `aldeas_caserios_2025` | Número de aldeas y caseríos usado en el cálculo. |
| `campos_suprimidos` | Lista de campos cuyo valor se ocultó por secreto estadístico. |
| `tiene_supresion` | `true` si la fila tiene al menos una celda suprimida. |
| `presion` | Percentil, puesto nacional, puesto departamental y clase por indicador. |

---

## 8. Pruebas

```bash
uv run pytest
```

La suite incluye 32 pruebas:

- **Normalización:** códigos de 2 y 4 dígitos, cruce +21 de los 16 municipios,
  ausencia de colisiones y rechazo de códigos inválidos.
- **Supresión:** conteos 1–4, ceros, valores faltantes, banderas por campo y
  supresión de tasas derivadas.
- **Descarga:** archivo `.xlsx` faltante descargado y manifestado con URL, fecha
  UTC y SHA-256; archivo existente no se vuelve a descargar; archivo local con el
  nombre original del publicador se reutiliza; HTML de error se rechaza; ruta
  específica del banco de datos del INE.
- **Integración:** 340 municipios sin códigos descartados, 22 departamentos,
  16 cruces +21, traslape 2015–2030 con diferencia 0, licencias en cada serie,
  SEGEPLAN no comercial, MINEDUC CC0, procedencia de cada salida, Parquet con
  340 filas y supresión conservada como `null`.

También se verificó:

```bash
cd web
pnpm typecheck
pnpm build
```

---

## 9. Uso de inteligencia artificial

Este prototipo fue desarrollado con asistencia de **DeepSeek V4.1 Flash a través
de OpenCode** para:

- estructurar el pipeline y la interfaz;
- escribir y revisar código y pruebas;
- redactar esta documentación.

**Ninguna cifra fue generada por IA.** Todos los valores provienen de los archivos
oficiales descargados y se procesan con código reproducible. El equipo revisa,
comprende y asume la responsabilidad del código, de la interpretación de los datos
y de las conclusiones. La declaración también aparece en la pestaña "Fuentes y
licencias" y en el pie de la aplicación.

---

## 10. Limitaciones

1. **Las proyecciones son escenarios, no predicciones.** La serie 2015–2035 es la
   actualización 2020 y puede perder vigencia lejos del período de estimación.
2. **Dos vigencias de proyección.** La serie larga 2015–2030 usa códigos
   `0123`–`0138` para los 16 municipios del departamento de Guatemala; se aplica
   el cruce +21 y se valida el traslape, pero no se mezclan años fuera de
   2015–2030.
3. **MINEDUC llega a 2022.** La razón nacimientos 2025 / escuelas 2022 compara un
   numerador de 2025 con una oferta de 2022. Es una aproximación de carga, no una
   medida de alumnos por aula ni de capacidad instalada.
4. **Pobreza extrema incompleta.** No está publicada para 23 municipios; se muestra
   como `n.d.`, no como cero.
5. **La asignación 2026 es un cálculo.** No es ejecución presupuestaria. La
   población de referencia es la usada por SEGEPLAN en el cálculo.
6. **Las clases de presión son relativas.** Son percentiles dentro de los 340
   municipios, no umbrales oficiales ni una evaluación de desempeño.
7. **Supresión conservadora.** El umbral 5 es una decisión del prototipo, no una
   marca oficial de supresión del INE. Se aplica a conteos de hechos vitales y
   escuelas, no a montos administrativos ni a estimaciones de pobreza.
8. **Códigos desconocidos excluidos.** Los registros con código `2300` o `9999`
   (municipio desconocido o exterior) no se imputan. Se reportan en el manifiesto.
9. **Sin inferencia causal.** La herramienta describe asociaciones y presión
   relativa; no identifica causas ni efectos.
10. **No es un sistema oficial del INE.** No implica adopción, certificación ni
    respaldo interinstitucional.
11. **SEGEPLAN CC BY-NC 2.0.** Uso no comercial únicamente; cualquier reutilización
    comercial requiere autorización.
12. **Sin datos de capacidad o calidad educativa.** No incluye aulas, docentes,
    jornadas ni resultados de aprendizaje; la oferta escolar se aproxima por
    número de establecimientos y matrícula.

---

## 11. Mejoras posibles

- Incorporar los ciclos MINEDUC más recientes cuando se publiquen y separar
  primaria, básicos y diversificado.
- Añadir aulas, docentes y capacidad instalada para una medida de hacinamiento.
- Añadir intervalos de confianza de pobreza y pruebas de sensibilidad.
- Incorporar ejecución presupuestaria municipal para comparar asignación con gasto.
- Agregar mapas coropléticos por departamento y municipio.
- Exportar la tabla a CSV/Excel y generar fichas municipales imprimibles.
- Añadir pruebas de extremo a extremo con Playwright y verificación de accesibilidad.
- Parametrizar el umbral de supresión y documentar una regla institucional.
- Traducir la interfaz a idiomas mayas cuando existan validaciones con las
  comunidades.

---

## 12. Solución de problemas

**El puerto 3000 está ocupado**

```bash
cd web
pnpm exec next dev -p 3010
```

**El MINEDUC falla con `CERTIFICATE_VERIFY_FAILED`**

El proyecto incluye `truststore`, que usa el almacén de certificados del sistema
operativo. Si el problema persiste, actualice los certificados del sistema o
ejecute el pipeline en un entorno con la cadena completa.

**El INE devuelve 502 o 504**

El descargador reintenta 6 veces con espera exponencial. Si el portal sigue
inestable, espere y vuelva a ejecutar; los archivos ya descargados se reutilizan.

**La página dice "Faltan los datos procesados"**

```bash
uv run build-pressure
```

**Quiero una demostración sin red**

```bash
uv run build-pressure --skip-download
```

**Quiero verificar un archivo**

```bash
shasum -a 256 data/ine_nacimientos_2025.xlsx
```

Compare con `data/manifest.json` o con la tabla de hashes de este README.

---

## 13. Créditos

- **Datos:** Instituto Nacional de Estadística (INE), Ministerio de Educación
  (MINEDUC) y Secretaría de Planificación y Programación de la Presidencia
  (SEGEPLAN) de Guatemala.
- **Desarrollo:** equipo del Datatón INE 2026, con asistencia de IA declarada.
- **Código:** MIT. Consulte `LICENSE`.
- **Componentes de terceros:** Next.js (MIT), React (MIT), Tailwind CSS (MIT),
  shadcn/ui (MIT), Radix UI (MIT), Recharts (MIT), lucide-react (ISC), pandas
  (BSD-3-Clause), openpyxl (MIT), pyarrow (Apache-2.0), requests (Apache-2.0),
  truststore (MIT) y pytest (MIT). Cada paquete conserva su licencia original en
  `node_modules` o en el entorno de `uv`.

---

## 14. Mapeo rápido a los criterios de aceptación

| Criterio | Implementación | Evidencia |
|---|---|---|
| Descargar archivos faltantes y registrar URL, UTC y SHA-256 | `pipeline/download.py` | `data/manifest.json`, `data/processed/provenance.json`, `tests/test_download.py` |
| 340 municipios sin códigos descartados y cruce +21 | `pipeline/normalize.py`, `pipeline/projections.py` | `tests/test_normalize.py`, `tests/test_pipeline.py`, `data_quality` en el JSON |
| Fuente, fecha y licencia en cada indicador | `pipeline/build.py`, `web/src/components/sources-panel.tsx` | `indicators[].source_metadata`, `sources[]`, pestaña "Fuentes y licencias" |
| Supresión visible en UI y datos exportados | `pipeline/suppression.py`, `web/src/components/municipality-table.tsx` | `campos_suprimidos`, `§ <5`, `null` en Parquet/JSON, `tests/test_suppression.py` |
| Next.js + shadcn/ui ejecutable con `pnpm` y `uv` | `web/`, `pyproject.toml`, `uv.lock` | `pnpm build`, `uv run build-pressure`, este README |
