# PRD 3: Municipal demand and economic activity profile

## 1. Summary and objective
Build a territorial web application that combines the 2018 Census with the National Statistical Directory of Enterprises (DINESE), including a "time jump" selector to switch between the 2024 cross-section and the 2021 to 2022 series. The app helps local teams and analysts inspect population structure and registered business establishments across all 340 municipalities without treating coverage shifts as economic growth or inventing missing firm identifiers or employment figures.

## 2. Users and use cases
* **Municipal teams and local planners:** Inspect population, age groups, and registered establishments by economic activity section, legal status, and firm size for a chosen municipality[cite: 2].
* **Entrepreneurs and territorial analysts:** Explore establishment counts and populated places within a municipality while respecting statistical secrecy and dataset limits[cite: 2, 3].

## 3. Data sources and rigor rules
* **Automatic retrieval fallback:** Check whether the required `.xlsx` files already exist in the local project data folder. If any required spreadsheet is missing locally, download it directly from the official INE data bank (`datos.ine.gob.gt` or `www.ine.gob.gt`), record the exact download URL, UTC timestamp, and SHA-256 hash, and cache it locally so subsequent runs work offline[cite: 2, 3].
* **2018 Census and populated places:** Load Census 2018 Table A1 (total population, sex, age groups, urban and rural area) and populated place centroids (20,036 places, 340 municipalities, 22 departments), verified on November 23, 2026[cite: 2].
* **DINESE (2021, 2022, and 2024):** Load `dinese-2021.xlsx`, `dinese-2022.xlsx`, and `dinese-2024.xlsx` from `datos.ine.gob.gt`[cite: 2]. Normalize department and municipality pairs across all 340 canonical municipalities[cite: 2, 3].
* **Time jump and non-comparability rules:** Treat 2024 as a cross-section rather than a direct growth panel against 2021, because total records jumped from 312,923 in 2021 to 645,431 in 2024 (+106.3%) and legal status categories were recoded (from 30/29 categories to 15 in 2024)[cite: 2, 3]. When switching between the 2024 view and the 2021 to 2022 view, display a clear warning about coverage and classification changes, report only CIIU sections (21 sections), firm size, and legal status, and never invent firm IDs or employment counts that do not exist in DINESE[cite: 2, 3].
* **Populated place map filtering and privacy:** Exclude the 301 populated places ending in `999` and the 313 records without coordinates from point map layers, keep outputs strictly aggregated under statistical secrecy rules (Decreto-Ley 3-85), and display exact INE source URLs, UTC download timestamps, and CKAN license status[cite: 2, 3].

## 4. User interface and experience (Next.js and shadcn/ui)
* **Web framework and UI library:** Build the frontend with **Next.js** (TypeScript and Tailwind CSS) using **shadcn/ui** components for all selectors, cards, alerts, badges, charts, and data tables.
* **Top bar with time jump:** Place a prominent shadcn/ui Select or Tabs control to jump between **"2024 Snapshot (DINESE 2024 + Census 2018)"** and **"2021–2022 Series (DINESE 2021–2022 + Census 2018)"**, paired with a shadcn/ui Badge and Alert explaining coverage and recoding differences[cite: 2, 3].
* **Territory selector:** Provide shadcn/ui selectors for department and municipality across all 340 normalized municipalities.
* **Profile sections:** Render shadcn/ui Card blocks for population and age breakdown, bar charts by CIIU section, firm size, and legal status, and a filterable shadcn/ui Table of populated places in the selected municipality showing coordinates and noting excluded `999` or coordinate-free entries[cite: 2].

## 5. Architecture and technical requirements
* **Data preparation and joins (Python with `uv`):** Build a Python pipeline managed with `uv` (`pyproject.toml` and `uv.lock`) that checks for local `.xlsx` files first, fetches missing ones from the official INE data bank, normalizes 4-digit municipality codes, builds the 340/340 department-municipality crosswalk, separates the 2024 snapshot from the 2021 to 2022 series, and writes aggregated Parquet or JSON outputs with a provenance manifest[cite: 2, 3].
* **Frontend web application (Next.js with `pnpm`):** Manage dependencies and scripts with **`pnpm`** (`package.json` and `pnpm-lock.yaml`). Build the UI in **Next.js** with **shadcn/ui**, reading preprocessed local outputs via local Route Handlers or static build artifacts with no external cloud services or secret keys at runtime[cite: 2, 3].
* **Testing and documentation:** Add `pytest` tests verifying the 340/340 municipality crosswalk, exclusion of `999` and missing-coordinate places from map points, separation of the 2024 snapshot from 2021 to 2022, and missing `.xlsx` retrieval from the official INE data bank[cite: 2, 3]. Write `README.md` covering problem and users, architecture and stack, local setup and run commands with `uv` and `pnpm`, dataset URLs with UTC download dates, licenses, explicit AI tool disclosure, and limitations[cite: 2, 3].

## 6. Acceptance criteria
* Missing `.xlsx` datasets in the local project folder are downloaded from the official INE data bank and logged with URL, UTC timestamp, and SHA-256 hash[cite: 2, 3].
* The time jump control switches between the 2024 snapshot and the 2021 to 2022 series and shows the matching coverage and recoding notice[cite: 2, 3].
* All 340 municipalities are selectable, and DINESE metrics display by CIIU section, firm size, and legal status without firm IDs or fabricated employment counts[cite: 2, 3].
* Populated places with suffix `999` or missing coordinates are excluded from point map markers[cite: 2].
* The Next.js and shadcn/ui application installs and runs locally using documented `pnpm` and `uv` commands[cite: 2, 3].
