import fs from "node:fs";
import path from "node:path";

import { normalizeText } from "./query";
import type { Catalog, DictionaryEntry, Manifest, RecordItem, Summary } from "./types";

const DATA_DIR = path.join(process.cwd(), "data");

function readJson<T>(fileName: string): T {
  const filePath = path.join(DATA_DIR, fileName);
  if (!fs.existsSync(filePath)) {
    throw new Error(
      `No existe ${filePath}. Ejecute \`uv run python -m procurement_prices build\` para generar los datos.`,
    );
  }
  return JSON.parse(fs.readFileSync(filePath, "utf8")) as T;
}

let summaryCache: Summary | null = null;
let manifestCache: Manifest | null = null;
type StoredRecord = Omit<RecordItem, "s">;
let recordsCache: RecordItem[] | null = null;
let catalogCache: Catalog | null = null;
let dictionaryCache: DictionaryEntry[] | null = null;

export function loadSummary(): Summary {
  summaryCache ??= readJson<Summary>("summary.json");
  return summaryCache;
}

export function loadManifest(): Manifest {
  manifestCache ??= readJson<Manifest>("manifest.json");
  return manifestCache;
}

export function loadRecords(): RecordItem[] {
  if (recordsCache === null) {
    const stored = readJson<StoredRecord[]>("records.json");
    recordsCache = stored.map((record) => ({
      ...record,
      s: [
        record.item,
        record.category,
        record.metric,
        record.unit,
        record.region,
        record.level,
        record.context,
        record.nog,
      ]
        .map((part) => normalizeText(part))
        .join(" "),
    }));
  }
  return recordsCache;
}

export function loadCatalog(): Catalog {
  catalogCache ??= readJson<Catalog>("catalog.json");
  return catalogCache;
}

export function loadDictionary(): DictionaryEntry[] {
  dictionaryCache ??= readJson<DictionaryEntry[]>("dictionary.json");
  return dictionaryCache;
}
