# PRD 4: Municipal Procurement Support with Reference Prices and Inputs

## 1. Summary and objective
Build a pre-quoting lookup and audit web application for municipal procurement and administrative teams, combining available Reference Price (DPIR) records, the Construction Materials Price Index (IPMC), the Construction Cost Index (ICC), and Basic Food Baskets (CBAU and CBAR). The app helps buyers inspect observed price bands, real data cutoff dates, and data quality anomalies before using a figure as a reference.

## 2. Users and use cases
* **Municipal buyers and procurement units:** Check historical price ranges, indices, and publication dates before preparing quotes or bidding specifications.
* **Administrative reviewers:** Spot invalid dates, exact duplicates, thousands commas, or frozen series before relying on a record.

## 3. Data sources and rigor rules
* **Automatic retrieval fallback:** Check if the required `.xlsx` and `.csv` files already exist in the local project data folder. If any required spreadsheet or table file is missing locally, retrieve it from the official INE data bank (`datos.ine.gob.gt` or `www.ine.gob.gt`), record the exact download URL, UTC timestamp, and SHA-256 hash, and cache it locally so subsequent runs work offline.
* **Reference prices (DPIR):** Load CKAN files frozen at June 2022 (`base-de-datos-pr-actualizados-hasta-junio-2022.csv`), August 2023 (`precios-de-referencia-al-02102023.xlsx`), and `diccionario-pr.xlsx` (verified November 23, 2026). Do not treat DPIR as a continuous monthly time series or promise full historical series. Clean or flag invalid dates such as `30/11/-0001`, exact duplicates, missing NOG values, and thousands commas in price fields.
* **Construction and baskets:** Load `HISTORICO-OCTUBRE.xlsx` (IPMC, 89 materials, base December 2018 = 100), `Historico-ICC_VSB_OCTUBRE..xlsx` (ICC, 2026 and Region I only), and 2024 to 2026 basket files (`costo-cba-percapita_u.xlsx`, `costo-cba-percapita_r.xlsx`, `historico-cbau_es_2024-2026.xlsx`, `historico-cbar_es_2024-2026.xlsx`). Always display the true cutoff date of the latest data inside each file, such as when an October file ends at August.
* **Statistical secrecy and attribution:** Keep outputs aggregated with no individual bidder or firm identification, and display exact INE source URLs, UTC download dates, and CKAN license status.

## 4. User interface and experience (Next.js and shadcn/ui)
* **Web framework and UI library:** Build the frontend with **Next.js** (TypeScript and Tailwind CSS) using **shadcn/ui** components for search bars, selects, cards, badges, tables, alerts, and inputs.
* **Search and filters:** Provide a keyword search box for product, construction input, or category, a shadcn/ui Select for source type (DPIR, IPMC, ICC, or Baskets), and date or cutoff filters.
* **Range and cutoff cards:** Render shadcn/ui Card components displaying minimum, median, maximum, record count, and the real data cutoff date plus frozen or partial-coverage status for the active source.
* **Findings table and unit price checker:** Render a shadcn/ui Table of matching records with price, date, and shadcn/ui Badge quality flags for invalid dates, duplicates, commas, or frozen datasets, paired with a unit price checker input and shadcn/ui Alert that flags values falling outside the observed range.

## 5. Architecture and technical requirements
* **Cleaning and normalization (Python with `uv`):** Build a Python ingestion and cleaning pipeline managed with `uv` (`pyproject.toml` and `uv.lock`) that checks local `.xlsx`/`.csv` files first, downloads missing ones from the official INE data bank, parses numeric prices cleanly, flags invalid dates and duplicates while keeping provenance, normalizes IPMC and ICC series, and writes clean Parquet or JSON outputs with a provenance manifest.
* **Frontend web application (Next.js with `pnpm`):** Manage dependencies and scripts with **`pnpm`** (`package.json` and `pnpm-lock.yaml`). Build the UI in **Next.js** with **shadcn/ui**, reading preprocessed local outputs via local Route Handlers or static build artifacts with no cloud services or secret keys at runtime.
* **Testing and documentation:** Include `pytest` tests verifying numeric parsing with thousands commas, detection of invalid dates and duplicates, accurate median and range calculations, and missing `.xlsx` retrieval from the official INE data bank. Write `README.md` covering problem and users, architecture and stack, local setup and run commands with `uv` and `pnpm`, dataset URLs with UTC download dates, licenses, explicit AI tool disclosure, and limitations.

## 6. Acceptance criteria
* Missing `.xlsx` or `.csv` datasets in the local data folder are fetched from the official INE data bank and logged with URL, UTC timestamp, and SHA-256 hash.
* Each source displays its real data cutoff date and whether it is frozen or limited in scope.
* Records with invalid dates, duplicates, or commas are flagged clearly and do not break numeric summaries.
* The unit price checker evaluates a test price against the active observed range and shows a clear status.
* The Next.js and shadcn/ui application installs and runs locally using documented `pnpm` and `uv` commands[cite: 2].
