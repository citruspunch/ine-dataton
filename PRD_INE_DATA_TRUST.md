# PRD v2.1: INE Data Trust, modular monorepo architecture

**Working title:** INE Data Trust. Does not imply certification, approval, or adoption by INE.
**Track:** Category 2, Technology and Data Science, Dataton INE 2026.
**Toolchain:** `uv` for Python, `pnpm` for Node.js and Next.js. No `make` or `Makefile`.
**Institutional fit:** Expands format verification (Step 5) and pre-publication review in Procedure 18 of the INE Directorate of Informatics Process Manual.

---

## 1. Purpose and scope boundaries

INE Data Trust validates published statistical aggregates before release or consumption, and exposes approved aggregates through a read-only snapshot. It acts as a technical check aligned with Procedure 18, not a replacement for `datos.ine.gob.gt`.

The system checks files against declarative YAML contracts, flags SHA-256 identity mismatches, summarizes declared variables, units and reference scopes, records human gate sign-offs, computes a timestamp-free `decision_basis_digest`, and exports a technical receipt. It does not publish to CKAN, does not process or anonymize raw microdata, does not auto-correct data values, and does not certify data on behalf of INE.

---

## 2. Repository folder layout and tooling

The repository separates concerns into distinct top-level directories so frontend, deterministic validation logic, MCP adapter, data stores, and tests stay decoupled[cite: 3, 4].

```text
ine-data-trust/
  web/                  Next.js, TypeScript, Tailwind CSS, shadcn/ui
  engine/               Deterministic Python validation core, managed with uv
  mcp/                  Optional P1 read-only MCP server, managed with uv
  profiles/             Declarative YAML rule contracts
  stores/
    review_store/       Private local review queue, candidates, fixtures, logs
    public_snapshot/    Approved aggregates, receipts, printable sheets, read view
  tests/                Python pytest suite and frontend checks
  docs/                 README, third-party licenses, AI usage note, pitch PDF, video
Tooling rules without make
Python environment and execution: Manage dependencies with pyproject.toml and uv.lock, and run commands via uv run.   
INVENTARIO_DATOS_INE.md
+ 1
Node.js and Next.js execution: Manage dependencies in web/package.json and pnpm-lock.yaml, and run scripts via pnpm --dir web.   
INVENTARIO_DATOS_INE.md
+ 1
Task entrypoints without make: Define runner scripts in root package.json using pnpm and uv run (for example, pnpm run dev:engine, pnpm run dev:web, pnpm run test:engine, and pnpm run demo:offline). Do not use Makefile or make targets.   
INVENTARIO_DATOS_INE.md
+ 1
Offline operation: After preparing local fixtures and verified INE samples, run validation, review, and demo flows without network access.   
PRD_INE_DATA_TRUST.md
3. Core features
3.1 Rule profile selector, YAML editor, and file upload
Profile dropdown: Lists existing YAML contracts from profiles/ (such as ipc_empalme_republica_v1.yaml, ipc_regional_v1.yaml, and contrato_mensual_v1.yaml).
Add new rule button: Opens a shadcn/ui dialog with a YAML editor and a local .yaml or .yml upload control.
Contract validation: Before saving a new profile to profiles/, the Python engine checks YAML syntax, required fields (expected_sheet, header_row, schema, types, grain, dates), column metadata (unit, reference scope, nullable, notes), and allowed column types (integer, float, string, date), returning clear field errors on invalid input.

PRD_INE_DATA_TRUST.md
3.2 Review queue and live file validation (stores/review_store/)
Live data upload and 1-click cases: Users can upload a local .csv, .xlsx, or .xls file or trigger preset cases:
Real CPI Republic splice (ipc_emprepu_es25.xlsx, Hoja2, showing official +0.50% for January 2025).   
INVENTARIO_DATOS_INE.md
+ 1
Second real CPI dataset (ipc_porreg_es25.xlsx or ipc_divgasto_25.xlsx) validated using a second YAML profile without changing Python validation code.   
INVENTARIO_DATOS_INE.md
+ 1
Variables and units summary (E and F indices with their own bases, plus published monthly variation G).
PRD_INE_DATA_TRUST.md
Synthetic failure fixtures: missing required column, duplicate grain, unexpected sheet name (expected_sheet vs. observed_sheets), and SHA-256 collision with mismatched identity.   
PRD_INE_DATA_TRUST.md
Semantic rules over fixed coordinates: Parse columns and periods by semantic schema definitions in YAML, keeping Excel cell coordinates strictly as informational evidence inside findings.   
PRD_INE_DATA_TRUST.md
Rule results table: Shows rule ID, severity, status (ok, advertencia, falla, no_evaluado), SHA-256 hash, and exact evidence.   
PRD_INE_DATA_TRUST.md
3.3 Human gate and live digest invalidation
Approval rules: Critical failures or unevaluated critical rules keep the item in no_habilitado. Warnings require an owner, justification, and decision in decision_log before promotion.
Canonical digest: Compute decision_basis_digest over file hashes, profile version, rule version, and findings, excluding execution and decision timestamps.
Live invalidation test: Include a button in review that mutates a candidate byte or rule parameter, recalculates decision_basis_digest, and revokes habilitado_para_consulta.

PRD_INE_DATA_TRUST.md
3.4 Public snapshot view and receipt export (stores/public_snapshot/)
Approved items only: Renders aggregates promoted through the human gate, with source, URL, UTC download timestamp, license (CC-BY where verified), base, period, variables and units summary, and decision_basis_digest.
Variables and units summary: Declares each column's internal name, header, type, unit, reference base or scope, nullability and notes, with valid, null and excluded counts plus coverage or caveat notes. It is dataset-agnostic.
Exports: Exports receipt.json (separating technical_payload and decision_log) and a clean printable validation sheet for Procedure 18 tickets.

PRD_INE_DATA_TRUST.md
3.5 Optional P1 read-only MCP server (mcp/)
Cutoff and isolation: Optional P1 component evaluated on November 25 at 12:00. Runs over stdio using the Python MCP SDK with uv run, reading only stores/public_snapshot/.
Boundaries: No access to stores/review_store/, no write operations, no remote calls, and no embedded LLM. Exposes list_enabled_aggregates and get_aggregate_receipt using the public snapshot contract, including the variables and units summary.

PRD_INE_DATA_TRUST.md
4. States, compliance, and deliverables
Explicit statuses
borrador: Incomplete snapshot or metadata card.   
PRD_INE_DATA_TRUST.md
no_habilitado: Critical failure or unevaluated critical rule[cite: 4].
en_revision: No critical failures, but warnings or human gate steps remain open[cite: 4].
habilitado_para_consulta: Critical checks passed, license verified, warnings justified, and human gate recorded[cite: 4].
cerrado: Closed by default due to missing license, permission, or evidence[cite: 4].
Dataton compliance and required files
Git history: Active Git repository from Day 1 with commits across team members and no prior project reuse.
Privacy and security: Published aggregates and labeled synthetic fixtures only, no microdata rows or personal/firm identifiers, and zero secrets or credentials in code.
Documentation: README.md (problem, users, folder architecture, uv and pnpm setup, INE datasets with exact URLs and UTC download dates, licenses, limitations), LICENSES_THIRD_PARTY.md, explicit AI tool disclosure, 7-minute PDF deck, and 2 to 3 minute backup video.
