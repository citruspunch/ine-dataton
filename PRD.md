# PRD 1: Cost of Living and Basic Food Basket Simulator

## 1. Summary and Objective
Build an interactive web application that lets citizens, households, and analysts calculate the monthly cost of Guatemala's Urban and Rural Basic Food Baskets (CBAU and CBAR, 2024 to 2026), inspect the cost per 1,000 kilocalories by food item, and check Consumer Price Index (CPI / IPC) variations using the official spliced series. The system prevents direct comparisons across un-spliced CPI base years and excludes zero-calorie items when computing caloric costs[cite: 2].

## 2. Users and Use Cases
* **Citizens and households:** Estimate monthly food expenses based on household size (1 to 8 members) and area (urban or rural)[cite: 2].
* **Students, educators, and journalists:** Compare item weights, inspect the cost per 1,000 kcal, and understand why mixing CPI base years without the official splice distorts results[cite: 2].

## 3. Data Sources and Rigor Rules
* **Automatic retrieval fallback:** Check if the required `.xlsx` and `.xls` files already exist in the local project data folder. If any required spreadsheet is missing locally, retrieve it directly from the official INE data bank (`datos.ine.gob.gt` / `www.ine.gob.gt`), log the exact download URL, UTC timestamp, and SHA-256 hash, and cache it locally so subsequent runs work offline[cite: 2, 7].
* **CBAU and CBAR (2024 to 2026):** Load `costo-cba-percapita_u.xlsx`, `costo-cba-percapita_r.xlsx`, `historico-cbau_es_2024-2026.xlsx`, and `historico-cbar_es_2024-2026.xlsx` from `datos.ine.gob.gt` (verified November 23, 2026). Multiply daily per-capita cost by 30 for the monthly per-capita cost and scale by household size[cite: 2].
* **CPI and official splice:** Load `ipc_2024_datosabiertos.xls` (base December 2023 = 100), `base-de-datos-ipc-ano-2025_es.xls` (base 2024 = 100), and `ipc_emprepu_es25.xlsx` (Republic splice). Never concatenate series across different base years without applying the official splice factor. For example, the official January 2025 monthly variation is +0.50%, whereas an un-spliced direct calculation yields -0.67%[cite: 2].
* **Chronological ordering and calories:** Map Spanish month names to integers 1 through 12. Never sort month labels alphabetically, as "Septiembre" sorts after "Octubre". In the cost per 1,000 kcal mode, exclude or flag zero-calorie items such as salt and water[cite: 2].
* **Attribution and licensing:** Always display the INE source, exact URL, UTC download date, and CKAN dataset license status[cite: 2, 7].

## 4. User Interface and Experience (Next.js + shadcn/ui)
* **Web framework and UI library:** Build the frontend with **Next.js** (TypeScript and Tailwind CSS) using **shadcn/ui** components for all controls, cards, alerts, badges, and data tables.
* **Layout:** Split the screen into a control panel on the left and household results on the right, topped by a methodological notice banner[cite: 2].
* **Controls:** Include a shadcn/ui Select or RadioGroup for area (Urban or Rural), a Slider for household members (1 to 8), Select dropdowns for month and year (January 2024 to October 2026), and a Switch or Tabs control to toggle between Total Monthly Cost and Cost per 1,000 kcal[cite: 2].
* **Top summary cards:** Render shadcn/ui Card components showing estimated monthly cost in quetzales, monthly or year-over-year variation using the official CPI splice, and daily kilocalories covered (referencing 2,052 kcal urban and 2,172 kcal rural)[cite: 2].
* **Visualizations and alerts:** Display a horizontal bar chart by food group and a sortable shadcn/ui Table listing products with unit price, caloric contribution, and cost per 1,000 kcal. Trigger a shadcn/ui Alert if the user attempts to compare periods across incompatible CPI base years without splicing or switches near the pre-2024 basket methodology break[cite: 2].

## 5. Architecture and Technical Requirements
* **Data ingestion and normalization (Python with `uv`):** Write a Python ingestion script managed with `uv` (`pyproject.toml` and `uv.lock`) that checks for local `.xlsx`/`.xls` files first, downloads any missing spreadsheets from the official INE data bank, normalizes numeric months and dates, applies the official CPI splice, and outputs clean Parquet or DuckDB tables alongside a provenance manifest[cite: 2].
* **Frontend web application (Next.js with `pnpm`):** Manage Node.js dependencies and scripts using **`pnpm`** (`package.json` and `pnpm-lock.yaml`). Build the UI in **Next.js** with **shadcn/ui**, reading the preprocessed local data via local Route Handlers or static build artifacts so runtime execution requires no external cloud services or secret keys[cite: 2, 6].
* **Testing and documentation:** Include `pytest` unit tests verifying chronological month sorting, exclusion of 0 kcal items in the 1,000 kcal calculation, local file fallback download behavior, and the official January 2025 CPI variation (+0.50%). Provide `README.md` covering problem and users, architecture and stack, local installation and execution via `uv` and `pnpm`, dataset URLs with UTC download timestamps, third-party licenses, explicit AI tool disclosure, and limitations[cite: 2, 7].

## 6. Acceptance Criteria
* If required `.xlsx` or `.xls` datasets are absent from the local project directory, the ingestion script fetches them from the official INE data bank and records their download metadata[cite: 2, 7].
* Monthly household cost scales accurately with the selected household size and urban/rural area[cite: 2].
* Switching to Cost per 1,000 kcal excludes zero-calorie items and displays valid caloric costs per food item[cite: 2].
* Attempting to compare months across un-spliced CPI base years triggers a clear shadcn/ui Alert and presents the official spliced figure[cite: 2].
* The Next.js and shadcn/ui application installs and runs locally using documented `pnpm` and `uv` commands[cite: 2].
