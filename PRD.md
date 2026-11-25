# PRD 2: Territory road safety and health radar

## 1. Summary and objective
Build a territorial web application to inspect 2025 births, deaths, traffic incidents, and injured or deceased road users in Guatemala, normalized as population rates and protected under statistical secrecy rules. The app helps users compare relative risk across territories without exposing small cells or mixing incompatible residence and occurrence definitions.

## 2. Users and use cases
* **Residents, students, and journalists:** Compare municipalities or departments using population-adjusted rates rather than raw counts.
* **Local analysts:** Separate place of residence from place of occurrence while respecting confidentiality thresholds.

## 3. Data sources and rigor rules
* **Automatic retrieval fallback:** Check if the required `.xlsx` files already exist in the local project data folder. If any required spreadsheet is missing locally, fetch it from the official INE data bank (`datos.ine.gob.gt` or `www.ine.gob.gt`), record the exact download URL, UTC timestamp, and SHA-256 hash, and cache it locally so later runs work offline.
* **2025 INE event datasets:** Load `nacimientos_2025.xlsx`, `defunciones_2025.xlsx`, `base-de-datos-hechos-de-transito-pnc-2025.xlsx`, `base-de-datos-fallecidos-y-lesionados-pnc-2025.xlsx`, and `base-de-datos-vehiculos-involucrados-pnc-2025.xlsx` from `datos.ine.gob.gt` (verified November 23, 2026).
* **Population and geography:** Load Census 2018 Table A1, populated place centroids (20,036 places, 340 municipalities, 22 departments), and 2015 to 2035 municipal projections. Apply the +21 code crosswalk on the 16 Guatemala department municipalities in long projections, and never mix census counts with projected population.
* **Residence vs. occurrence:** Keep place of residence and place of occurrence separate, and display which criterion is active on every view.
* **Statistical secrecy and map filtering:** Follow Decree-Ley 3-85 and its regulations by suppressing any cell with fewer than 5 cases (and fewer than 10 for homicides or suicides if broken out), grouping ages into five-year bands, avoiding fine municipality by day or cause/crime slices with small counts, and omitting vehicle make, color, and model from traffic views. Exclude the 301 populated places ending in `999` and the 313 records without coordinates from point map layers.

## 4. User interface and experience (Next.js and shadcn/ui)
* **Web framework and UI library:** Build the frontend with **Next.js** (TypeScript and Tailwind CSS) using **shadcn/ui** components for controls, cards, alerts, badges, and tables.
* **Layout:** Place an interactive map of Guatemala on the left and a territorial detail and privacy panel on the right.
* **Controls:** Provide shadcn/ui selectors for topic (Road safety, Births, or Deaths), territory criterion (Place of residence or Place of occurrence), geographic level (Department or Municipality), and a toggle between raw count and rate per 10,000 residents.
* **Map and side panel:** Shade territories by rate or count, render a filtered point layer without `999` or coordinate-free places, and show a shadcn/ui Card with the selected territory rate, baseline comparison, population denominator note, and a shadcn/ui Alert when a cell is suppressed for statistical secrecy.

## 5. Architecture and technical requirements
* **Processing and suppression (Python with `uv`):** Build a Python pipeline managed with `uv` (`pyproject.toml` and `uv.lock`) that checks for local `.xlsx` files first, downloads missing ones from the official INE data bank, normalizes 2-digit department and 4-digit municipality codes, applies the +21 crosswalk where needed, computes rates, applies cell suppression, and writes clean Parquet or JSON outputs with a provenance manifest.
* **Frontend web application (Next.js with `pnpm`):** Manage dependencies and scripts with **`pnpm`** (`package.json` and `pnpm-lock.yaml`). Build the UI in **Next.js** with **shadcn/ui**, reading pre-processed local outputs via local Route Handlers or static build files with no cloud dependencies or secret keys at runtime.
* **Testing and documentation:** Add `pytest` tests verifying that no suppressed cell exposes a numeric value, the 340-municipality crosswalk holds, and missing `.xlsx` files trigger the official INE retrieval fallback. Write `README.md` covering problem and users, architecture and stack, local setup and run commands with `uv` and `pnpm`, dataset URLs with UTC download dates, licenses, explicit AI tool disclosure, and limitations.

## 6. Acceptance criteria
* Missing `.xlsx` files in the local data directory are fetched from the official INE data bank and logged with URL, UTC timestamp, and SHA-256 hash.
* No cell below the suppression threshold displays a numeric value in the UI or in exported data.
* Users can switch between place of residence and place of occurrence and see the matching methodology note.
* Populated places with suffix `999` or missing coordinates are excluded from point map markers.
* The Next.js and shadcn/ui application installs and runs locally using documented `pnpm` and `uv` commands.
