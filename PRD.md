# PRD 5: Service pressure and local growth monitor

## 1. Summary and objective
Build a municipal comparison web application that pairs projected population growth and 2025 vital events from INE with verified public open datasets, including MINEDUC school and student records and SEGEPLAN municipal poverty and constitutional allocation data. The app helps local planners spot municipalities facing rising demand relative to local services using clean municipal code joins, clear license notices, and statistical secrecy rules[cite: 2, 3].

## 2. Users and use cases
* **Municipal planners and local development teams:** Compare municipalities within a department to see where population or births grow relative to school supply or municipal transfers[cite: 2].
* **Public policy analysts:** Review standardized municipal indicators with clear source provenance, license terms, and coverage limits[cite: 2, 3].

## 3. Data sources and rigor rules
* **Automatic retrieval fallback:** Check if the required `.xlsx` and `.csv` files already exist in the local project data folder. If any required file is missing locally, fetch it from the official INE data bank (`datos.ine.gob.gt` or `www.ine.gob.gt`) or the verified external open portals, log the exact download URL, UTC timestamp, and SHA-256 hash, and cache it locally so later runs work offline[cite: 2, 3].
* **INE datasets:** Load 2015 to 2035 and 2015 to 2030 municipal projections, 2025 births (`nacimientos_2025.xlsx`) and deaths (`defunciones_2025.xlsx`), and the 340-municipality reference catalog, verified on November 23, 2026. Normalize 2-digit department and 4-digit municipality codes, and apply the +21 code crosswalk on the 16 Guatemala department municipalities in long projections[cite: 2].
* **External open datasets:** Join verified MINEDUC datasets (schools and students, CC0 license) and SEGEPLAN datasets (municipal poverty and constitutional allocation, CC BY-NC 2.0 license) by 4-digit municipal code using 2-digit department plus 2-digit municipality codes[cite: 2, 3].
* **Licenses and statistical secrecy:** State clearly that SEGEPLAN datasets carry a CC BY-NC 2.0 license (non-commercial use) while MINEDUC datasets use CC0, and list exact INE source URLs, UTC download timestamps, and CKAN license status. Apply cell suppression for small counts under Decree-Ley 3-85 and its regulations, and do not present joins as an official inter-institutional INE system[cite: 2, 3].

## 4. User interface and experience (Next.js and shadcn/ui)
* **Web framework and UI library:** Build the frontend with **Next.js** (TypeScript and Tailwind CSS) using **shadcn/ui** components for selectors, cards, alerts, badges, charts, and tables.
* **Top controls:** Provide shadcn/ui selectors for department, pressure indicator (projected population growth, births relative to schools, or municipal allocations), and municipality search.
* **Charts and table:** Render a bar or scatter chart comparing municipalities alongside a sortable shadcn/ui Table of all 340 municipalities with normalized codes, indicator values, and suppression badges.
* **Sources and licenses tab:** Include a dedicated shadcn/ui Tabs panel or footer card listing each dataset (INE, MINEDUC, SEGEPLAN), download URL, UTC timestamp, exact license including CC BY-NC 2.0 non-commercial terms, and applied cell suppression rules[cite: 2, 3].

## 5. Architecture and technical requirements
* **Integration and joins (Python with `uv`):** Build a Python pipeline managed with `uv` (`pyproject.toml` and `uv.lock`) that checks for local `.xlsx` and `.csv` files first, downloads missing ones from the official INE data bank and verified open portals, standardizes 4-digit municipal codes, applies the +21 crosswalk on long projections, computes pressure indicators, applies cell suppression, and writes clean Parquet or JSON outputs with a provenance manifest[cite: 2, 3].
* **Frontend web application (Next.js with `pnpm`):** Manage dependencies and scripts with **`pnpm`** (`package.json` and `pnpm-lock.yaml`). Build the UI in **Next.js** with **shadcn/ui**, reading preprocessed local outputs via local Route Handlers or static build files with no cloud services or secret keys at runtime[cite: 2, 3].
* **Testing and documentation:** Add `pytest` unit tests verifying the 340-municipality join without dropped codes, the +21 crosswalk on the 16 Guatemala department municipalities, cell suppression on small counts, license metadata on every series, and missing `.xlsx` retrieval from the official INE data bank. Write `README.md` covering problem and users, architecture and stack, local setup and run commands with `uv` and `pnpm`, dataset URLs with UTC download dates, licenses, explicit AI tool disclosure, and limitations[cite: 2, 3].

## 6. Acceptance criteria
* Missing `.xlsx` or `.csv` files in the local data directory are downloaded from the official INE data bank or verified open sources and logged with URL, UTC timestamp, and SHA-256 hash[cite: 2, 3].
* All 340 municipalities join cleanly on normalized 4-digit codes with the +21 projection crosswalk applied[cite: 2].
* Every indicator displays its source, download date, and exact license, including the CC BY-NC 2.0 non-commercial notice where applicable[cite: 2, 3].
* Small-count cells are suppressed visibly in the UI and exported data[cite: 2].
* The Next.js and shadcn/ui application installs and runs locally using documented `pnpm` and `uv` commands[cite: 2, 3].
