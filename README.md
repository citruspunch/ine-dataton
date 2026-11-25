# Radar territorial de seguridad vial y salud — Guatemala 2025

A local-first territorial explorer for 2025 births, deaths, traffic incidents and road
users injured or killed in Guatemala. It turns raw INE event tables into comparable rates
per 10,000 residents, keeps **place of residence** and **place of occurrence** strictly
separate, and applies statistical-secrecy rules before anything reaches the screen.

Built for the **Datatón INE 2026** (Tecnología y ciencias de datos category).

![Next.js](https://img.shields.io/badge/Next.js-16-000?logo=nextdotjs)
![React](https://img.shields.io/badge/React-19-087ea4?logo=react)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-4-38bdf8?logo=tailwindcss)
![Python](https://img.shields.io/badge/Python-3.12-3776ab?logo=python)
![uv](https://img.shields.io/badge/uv-pipeline-de5fe9)
![License](https://img.shields.io/badge/code-MIT-green)

---

## 1. Problem and users

Guatemala publishes rich 2025 vital statistics and traffic records, but the raw tables are
hard to use responsibly:

- Counts are not comparable: Petén and Guatemala City have very different populations.
- “Where the person lived” and “where the event happened” are different variables that are
  easy to mix.
- Small municipalities and cause breakdowns can identify people if published without
  suppression.
- Spreadsheet downloads change over time and are hard to reproduce.

**Radar territorial** answers: *how does the relative risk of a territory compare with the
rest of the country, and which privacy-safe number supports that comparison?*

Primary users:

- **Residents, students and journalists** comparing departments or municipalities with
  population-adjusted rates instead of raw counts.
- **Local analysts** separating residence from occurrence and checking which cells are
  suppressed, and why.

## 2. What the application does

| Control | Options |
| --- | --- |
| Topic | Road safety · Births · Deaths |
| Indicator | Traffic incidents, fatalities and injuries; all deaths and a cause breakdown at department level; births |
| Territory criterion | **Place of residence** · **Place of occurrence** |
| Geographic level | 22 departments · 340 municipalities |
| Unit | Rate per 10,000 residents · raw count |
| Map layer | Filtered populated-place centroids (19,723 points) |

- The left side is an interactive SVG map of Guatemala shaded by rate or count. Click a
  territory, hover for a tooltip, zoom with the wheel/double click or the buttons.
- The right side shows the selected territory: rate, count, national baseline, relative
  risk, rank, projected population, census reference, a compact cause breakdown for
  deaths at department level, and the privacy note.
- Every map, detail card, table and sheet displays the **active territorial criterion** and
  its methodology note.
- The bottom table can search and sort all 22 departments or 340 municipalities, and
  distinguishes **published**, **suppressed** and **not available** cells.
- A “Metodología” sheet lists sources with URL, UTC retrieval time, SHA-256, licenses,
  limitations and the AI disclosure.

Road-safety data are published by the PNC **by occurrence only**. Selecting “residence” for
road safety does not invent a variable: the map and detail panel show an explicit
“not available” state with the reason and a one-click switch back to occurrence.

## 3. Architecture and stack

```text
INE CKAN (datos.ine.gob.gt) + geoBoundaries/OCHA
                 │
                 │ local-first: use cached file if valid, otherwise download
                 │ SHA-256 + UTC timestamp + URL in a manifest
                 ▼
data/raw/*.xlsx  ──  data/reference/*.geojson + municipal crosswalk CSV
                 │
                 │ Python 3.12 · uv · pandas · openpyxl
                 ▼
radar/build.py   ──  normalise codes → +21 crosswalk → aggregate → suppress
                 │
                 ▼
web/public/data/*.json + *.geojson  (no cloud, no secrets, no runtime API key)
                 │
                 ▼
Next.js 16 App Router · React 19 · TypeScript · Tailwind CSS 4
shadcn/ui (Radix) · d3-geo · lucide-react
```

- **Pipeline:** Python package `radar/`, managed with **uv** (`pyproject.toml`, `uv.lock`).
- **Frontend:** Next.js with **pnpm** (`web/package.json`, `web/pnpm-lock.yaml`).
- **Data access at runtime:** static pre-processed files under `web/public/data`. The app
  fetches only its own local files; it has no database, cloud service, API key or external
  map tiles. Map geometry is rendered locally with `d3-geo`.
- **Offline:** after one successful retrieval, `uv run radar build --offline` works without
  network. The processed JSON is committed, so the frontend also runs without Python.

### Repository layout

```text
radar/                     Python pipeline
  config.py                official URLs, thresholds, labels
  fetch.py                 local-first retrieval + provenance manifest
  normalize.py             code normalisation and +21 crosswalk
  reference.py             census, projections, centroids, GeoJSON
  suppress.py              statistical-secrecy cells
  build.py                 indicators, causes, age bands, outputs
  cli.py                   `uv run radar build|fetch|verify`
tests/                     pytest: crosswalk, suppression, fallback, points, outputs
data/
  raw/                     cached INE .xlsx (git-ignored)
  reference/               municipal crosswalk + cached GeoJSON (GeoJSON git-ignored)
  processed/               copies of the JSON outputs for analysts
web/
  app/                     Next.js App Router page and styles
  components/              shadcn/ui primitives + map/detail/methodology components
  lib/                     types, data loading, colours, formatting, d3 winding fix
  public/data/             committed processed outputs consumed by the app
```

## 4. Data sources and provenance

All sources below were retrieved on **2026-11-25 (UTC)** from the official INE data bank
(`datos.ine.gob.gt`). The source list was verified against the portal on 2026-11-23. The
pipeline records the exact URL, retrieval time and SHA-256 of every file in
`data/raw/provenance.json` and `data/reference/provenance.json`; the app exposes them in
the methodology sheet.

### 4.1 2025 event tables

| File | UTC retrieved | Bytes | License |
| --- | --- | ---: | --- |
| `nacimientos_2025.xlsx` | 2026-11-25T04:43:12Z | 39,102,416 | INE open data; no explicit license in catalogue, attributed |
| `defunciones_2025.xlsx` | 2026-11-25T04:43:12Z | 8,918,540 | INE open data; no explicit license in catalogue, attributed |
| `base-de-datos-hechos-de-transito-pnc-2025.xlsx` | 2026-11-25T04:43:12Z | 666,547 | CC BY (INE / PNC) |
| `base-de-datos-fallecidos-y-lesionados-pnc-2025.xlsx` | 2026-11-25T04:43:12Z | 1,309,998 | CC BY (INE / PNC) |
| `base-de-datos-vehiculos-involucrados-pnc-2025.xlsx` | 2026-11-25T04:43:12Z | 1,462,360 | CC BY (INE / PNC) |

### 4.2 Population and geography

| File | UTC retrieved | Bytes | License |
| --- | --- | ---: | --- |
| `proyecciones_poblacion_2015_2030.xlsx` | 2026-11-25T04:43:12Z | 7,775,292 | ODC-BY (INE) |
| `censo_2018_cuadro_a1.xlsx` | 2026-11-25T04:43:12Z | 4,072,815 | CC BY (INE) |
| `centroides_lugares_poblados_2018.xlsx` | 2026-11-25T04:43:12Z | 1,105,747 | CC BY (INE) |
| `gtm_adm1.geojson` (departments) | 2026-11-25T05:21:29Z | 318,584 | CC BY 3.0 IGO (OCHA FISS / geoBoundaries) |
| `gtm_adm2.geojson` (municipalities) | 2026-11-25T05:21:29Z | 1,162,585 | CC BY 3.0 IGO (OCHA FISS / geoBoundaries) |

### 4.3 Exact download URLs

```text
https://datos.ine.gob.gt/dataset/96888fc0-5ced-4a58-bfd0-2a6a292e3208/resource/b6847c70-a0b9-4cfd-a405-4ea4360905d7/download/nacimientos_2025.xlsx
https://datos.ine.gob.gt/dataset/14f547c3-ad37-4ea1-9e74-16a3ed50ff54/resource/43adb351-0a14-4783-8401-e5ef21a2222e/download/defunciones_2025.xlsx
https://datos.ine.gob.gt/dataset/1960f9e0-93a2-4e12-9692-8867b8150a54/resource/dc29a0a2-31b2-49d8-a047-aa9bd6f2afcb/download/base-de-datos-hechos-de-transito-pnc-2025.xlsx
https://datos.ine.gob.gt/dataset/b80e7836-a158-4830-9177-bca5a3b6cf0d/resource/2ffc0ffd-74f5-4cae-bbd8-6fa0698e3492/download/base-de-datos-fallecidos-y-lesionados-pnc-2025.xlsx
https://datos.ine.gob.gt/dataset/a241d504-1c89-49d2-a490-a73cfc21276d/resource/a157bee0-1e72-448f-8fc7-399ba7b9606d/download/base-de-datos-vehiculos-involucrados-pnc-2025.xlsx
https://datos.ine.gob.gt/dataset/23bbe8f8-ec9b-49c9-bcca-de78bec4efc0/resource/56b97bc0-5624-408d-a136-3931dd05610a/download/estimaciones-y-proyecciones-de-la-poblacion-total-por-municipio-segun-sexo-y-edad.-2015-2030.xlsx
https://datos.ine.gob.gt/dataset/78019333-d80b-45e8-b694-fb3b8d65e19e/resource/4b9c7220-ca0c-41a9-a121-348f533b070e/download/cuadro-a1-poblacion-total-censada-por-sexo-grupos-quinquenales-de-edad-y-area.xlsx
https://datos.ine.gob.gt/dataset/78019333-d80b-45e8-b694-fb3b8d65e19e/resource/053dfa99-b3f9-4b1f-a99f-fc933ef00da4/download/centroides-de-lugares-poblados-de-la-republica-de-guatemala.-censo-2018.xlsx
https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/GTM/ADM1/geoBoundaries-GTM-ADM1_simplified.geojson
https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/GTM/ADM2/geoBoundaries-GTM-ADM2_simplified.geojson
```

<details>
<summary><strong>SHA-256 digests of the cached files</strong></summary>

```text
nacimientos_2025.xlsx
12dd75c254f3c37e2637fb76ee6a5e1b11ffdfcec738f90e46a16605945b39e9
defunciones_2025.xlsx
332da4f661f78db0eab9788450fffaea68f4eedd22febac100790600c51870a7
base-de-datos-hechos-de-transito-pnc-2025.xlsx
1c44e796adb426354cd7d3fddf3250634f3b794081531fcc7b88d87e203180a9
base-de-datos-fallecidos-y-lesionados-pnc-2025.xlsx
c022c4b10776f92af919b9d19bea58c330adc4119c05954fddde4853bd1bd275
base-de-datos-vehiculos-involucrados-pnc-2025.xlsx
81d9e4793efe31c14b5c936d38fdee75fabf2e1a446cae79096164b809d54224
proyecciones_poblacion_2015_2030.xlsx
b00fa494491b5b06e2fb7dac98df2441b6670e8d9a748cc97c2e72ed5012f499
censo_2018_cuadro_a1.xlsx
b4dfbc6a0373373e8f35827ef5a8d5ed07db5d035225a271061b1869769e96d9
centroides_lugares_poblados_2018.xlsx
b8ea8fea33e6d606e102e8d96ed692deacec660c028ffcf673f84459bcafe14e
gtm_adm1.geojson
7f84a4e2a8773953af1c602c67f27457b093e3cfc6ab21052446b172b71d7628
gtm_adm2.geojson
04ec4cacdc6c1aa01b4e67ccea28fe4b8f9fa758047a6c7d666668171e95eb94
```

</details>

## 5. Methodology and data-rigour rules

### 5.1 Residence vs occurrence

Every event table carries two territorial variables:

- `Depreg` / `Mupreg` — **residence** of the person (mother, deceased, etc.).
- `Depocu` / `Mupocu` — **occurrence** of the event (birth, death, crash).

They are aggregated separately and never summed. Every view states which criterion is
active. A rate by occurrence uses the territory’s **resident population** as a reference
denominator; it does not measure the population exposed at the event location. The UI says
so explicitly.

The PNC traffic tables only have `depto_ocu` / `mupio_ocu`. For road safety, the residence
criterion is therefore marked **not available**; no proxy or imputation is used.

### 5.2 Codes, the +21 crosswalk and the 340 municipalities

- Municipality codes are normalised to four digits (`107` → `0107`, `2214` → `2214`).
- Census 2018 uses `0101–0117` for the Guatemala department. The 2015–2030 projections
  keep `0101` (Guatemala City) and renumber the other 16 municipalities as `0123–0138`.
  The pipeline applies **+21** to census codes `0102–0117`; all other 324 codes are
  unchanged. The function is idempotent for already-projected codes.
- The municipal name/code/boundary crosswalk is stored in
  `data/reference/municipios_crosswalk.csv`: **340 unique codes**, **22 departments** and
  **340 unique boundary features**. The validation test fails if any of these invariants
  break.
- Two geoBoundaries polygons for lakes (`Lago de Amatitlán`, `Lago de Atitlán`) are
  excluded; they are not municipalities.
- The single death record with occurrence code `0930` is not a municipality in the
  340-code crosswalk. It is excluded from territorial totals and reported in the data
  diagnostics; the national occurrence count is 96,063 vs. 96,064 raw records.

### 5.3 Rates and denominator

```text
rate per 10,000 = cases in 2025 / projected total population 2025 × 10,000
```

- Denominator: **INE municipal projections 2025, both sexes** (`SEXO = 0`).
- National population used by the build: **18,079,810**.
- The 2018 census count is displayed only as a reference and is **never** used as a rate
  denominator.
- Births: 286,539 (occurrence year 2025, including registrations processed in 2026).
- Deaths: 96,064 raw records occurred in 2025; 96,063 mapped to a territory.
- Traffic: 8,881 incidents, 2,432 fatalities, 9,599 injuries, 13,822 vehicles involved
  (2 victim records have an ignored `fall_les` status and are not counted as either).
- Rates are crude (not age-standardised). Differences may partly reflect age structure;
  the age profile is exposed at department level to make that visible.

### 5.4 Statistical secrecy (Decreto-Ley 3-85)

- Any cell with **fewer than 5 cases** is suppressed. Zero cells are also suppressed, as
  required by the PRD (“any cell with fewer than 5 cases”).
- **Homicides and suicides** broken out by territory use a threshold of **10**.
- A suppressed cell is exported only as `{"suppressed": true, "threshold": n}`. It has **no
  `count` and no `rate`** key. Rates are hidden too, because with a public denominator a
  rate would let a user reconstruct the count.
- The UI shows “—” and a “Suprimido” badge/alert; it never displays a number for a
  suppressed cell. The map uses a hatched fill and the tooltip says “Celda suprimida”.
- No municipality × day slices are published. Cause breakdowns at municipality level are
  suppressed with the same thresholds. Age profiles are published only at national and
  department level, in five-year bands (the last band is open `80+`).
- Vehicle make, colour and model are **never selected, aggregated or exported**; the
  vehicle table appears only as a count of vehicles involved.
- Age code `999` (unknown) is treated as “Ignorada”, not as age 80+; it is reported in a
  footnote rather than plotted as a bar.

### 5.5 Populated-place point layer

The source has **20,036 populated places** (after removing the footer row and the two
header rows). The map layer excludes:

- **301** places whose code ends in `999` (“Otros Lugares Poblados”);
- **313** records without longitude/latitude.

All 301 `999` places are a subset of the 313 coordinate-less records, so the union is
**313 excluded** and **19,723 visible points**. The map and methodology sheet state this
overlap explicitly. Points are settlement geography from Census 2018, not event locations.

### 5.6 Projection horizon

The PRD mentions 2015–2035 municipal projections. The official INE data bank currently
publishes the municipal series **2015–2030** (verified 2026-11-23). The pipeline uses the
2025 column from that official series and does **not** extrapolate to 2035. This is
documented in the methodology sheet and in the limitations.

## 6. Local setup and run

### Prerequisites

- Python **3.11+** and [uv](https://docs.astral.sh/uv/)
- Node.js **20.9+** and [pnpm](https://pnpm.io/) 10+
- Network access for the first retrieval; none afterwards

### 6.1 Build the data

```bash
# from the repository root
uv sync
uv run radar build
```

`radar build` checks `data/raw` and `data/reference` first. Only missing or corrupt files
are downloaded from the official URLs. The manifest is written to
`data/raw/provenance.json` and `data/reference/provenance.json`, and the provenance is
embedded in `web/public/data/meta.json`.

Useful commands:

```bash
uv run radar fetch            # only retrieve/verify sources
uv run radar build --offline  # build with cached files; fail if a source is missing
uv run radar verify           # privacy, 340-municipality, 22-department and point invariants
uv run pytest                 # 22 tests
```

The processed outputs are committed in `web/public/data`, so the frontend can run without
running Python first. Re-run `uv run radar build` after changing the pipeline.

### 6.2 Run the frontend

```bash
cd web
pnpm install
pnpm dev
```

Open <http://localhost:3000>.

Production build:

```bash
cd web
pnpm build
pnpm start
```

Type check:

```bash
cd web
pnpm typecheck
```

### 6.3 Test suite

```bash
uv run pytest -q
```

The 22 tests cover:

- the 340-municipality crosswalk and the exact +21 mapping;
- suppressed cells never exposing `count` or `rate` in any exported JSON;
- the 5-case and 10-case thresholds, including zero cells;
- missing/corrupt `.xlsx` files triggering the INE download fallback and logging URL,
  UTC timestamp and SHA-256;
- local files winning over the network;
- offline builds failing loudly when a source is missing;
- the 20,036 → 19,723 point filter (301 `999` + 313 without coordinates, overlapping);
- 340 municipal and 22 departmental GeoJSON features;
- rate arithmetic against projected population;
- criterion notes and the absence of vehicle make/colour/model in exports.

## 7. Outputs

`web/public/data/` (also copied to `data/processed/`):

| File | Contents |
| --- | --- |
| `meta.json` | Provenance, thresholds, definitions, limitations, licenses, AI disclosure |
| `territories.json` | 22 departments and 340 municipalities with projected 2025 and census 2018 population |
| `indicators.json` | Topic × metric × criterion × level counts, rates and suppressed cells |
| `death-causes.json` | All / homicide / suicide / traffic death cells, with thresholds |
| `age-profile.json` | Five-year age bands, national and departmental (exported for analysts; not shown in the current UI) |
| `points.json` | 19,723 filtered populated-place centroids (compact array schema) |
| `municipios.geojson` | 340 municipal polygons with `code`, `name`, `dept` |
| `departamentos.geojson` | 22 departmental polygons |

Suppressed cells are represented as `{"suppressed": true, "threshold": 5|10}` with no
numeric count or rate.

## 8. Acceptance criteria mapping

| PRD acceptance criterion | Implementation |
| --- | --- |
| Missing `.xlsx` fetched from INE and logged with URL, UTC timestamp, SHA-256 | `radar/fetch.py`; manifest in `data/raw/provenance.json`; test `test_fetch_fallback.py` |
| No cell below the threshold shows a numeric value in UI or exports | `radar/suppress.py`; export walk test; UI suppressed branches |
| Users switch residence/occurrence and see the matching note | Criterion selector, notes in `meta.criterionNotes`, `DetailPanel`; road safety shows “not available” |
| Populated places ending `999` or without coordinates excluded | `radar/reference.py`; 19,723 points; `test_points.py` |
| Next.js + shadcn/ui app installs and runs with documented `pnpm`/`uv` | This README; `web/pnpm-lock.yaml`; `uv.lock`; `pnpm dev` |

## 9. Licenses and attribution

- **INE data:** Instituto Nacional de Estadística de Guatemala. The traffic, census and
  populated-place datasets are listed as **CC BY**; the municipal projections as
  **ODC-BY**. The births and deaths datasets have no license field in the INE catalogue;
  they are used as open government data with attribution. Cite INE in any reuse.
- **Boundaries:** geoBoundaries / OCHA FISS, **CC BY 3.0 IGO**. Source:
  <https://www.geoboundaries.org/>.
- **Code:** **MIT** (see `LICENSE`).
- **Third-party components:** Next.js (MIT), React (MIT), Tailwind CSS (MIT), shadcn/ui
  (MIT), Radix UI (MIT), d3-geo (ISC), lucide-react (ISC), Inter and Fraunces
  (SIL Open Font License, via `@fontsource-variable`). Their original licenses apply.
- **Statistical secrecy:** Decreto-Ley 3-85 (Ley Orgánica del INE) and its regulations.

## 10. AI tool disclosure

This project was developed during the Datatón INE 2026 with assistance from generative AI
tools: **OpenCode** as the coding agent and **DeepSeek V4.1 Flash** as the underlying
language model. AI assisted with code generation, refactoring, test writing, UI
implementation and documentation. The team reviews, runs and can explain the code and the
methodological decisions. No AI model was used to invent, impute or alter official data;
all figures come from the cited INE files and are reproducible with the commands above.

## 11. Limitations and possible improvements

- PNC traffic records have no residence variable. Road-safety residence views are
  intentionally unavailable rather than imputed.
- Official municipal projections stop at 2030; the app does not extrapolate to 2035.
- One death record uses occurrence code `0930`, which is not a municipality in the
  340-code crosswalk. It is excluded from territorial totals and reported.
- A non-trivial share of birth records has unknown mother’s age (`999`); the age profile
  reports it separately instead of imputing it.
- Rates are crude and not age-standardised. An age-standardised rate (direct or indirect)
  would improve comparisons between departments with different age structures.
- Municipal boundaries come from OCHA/geoBoundaries (2021), not from an official INE
  cartographic product. The name matching uses 22 explicit aliases (e.g. “San Juan
  Alotenango” → “Alotenango”); future boundary releases may require updating the
  crosswalk.
- The point layer shows settlements, not individual events. A future version could add
  privacy-safe hexbin or kernel layers if event coordinates become available.
- The map is a static TopoJSON/GeoJSON rendering with no basemap tiles; a hillshade or
  road network could improve orientation but would add external dependencies.
- Data are a snapshot. INE may revise 2025 files; the SHA-256 hashes pin the version used
  here. Re-run `uv run radar build` to refresh and compare hashes.

---

**Fuente de los datos:** Instituto Nacional de Estadística (INE), Guatemala · **Límites:**
geoBoundaries / OCHA FISS · **Año de eventos:** 2025 · **Denominador:** proyección
municipal 2025 · **Construido para:** Datatón INE 2026.
