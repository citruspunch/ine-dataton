import { PriceDesk } from "@/components/price-desk";
import {
  loadCatalog,
  loadDictionary,
  loadManifest,
  loadRecords,
  loadSummary,
} from "@/lib/data";
import { queryRecords } from "@/lib/query";

export default function Home() {
  const summary = loadSummary();
  const manifest = loadManifest();
  const catalog = loadCatalog();
  const dictionary = loadDictionary();
  const records = loadRecords();
  const base = queryRecords(records, summary, {
    source: "DPIR",
    q: "papel bond",
    page: 1,
    pageSize: 25,
  });
  const initialUnit =
    base.facets.units.length > 1 && base.facets.units.length <= 40
      ? base.facets.units[0].label
      : undefined;
  const initial = initialUnit
    ? queryRecords(records, summary, {
        source: "DPIR",
        q: "papel bond",
        unit: initialUnit,
        page: 1,
        pageSize: 25,
      })
    : base;

  return (
    <PriceDesk
      initial={initial}
      summary={summary}
      manifest={manifest}
      catalog={catalog}
      dictionary={dictionary}
    />
  );
}
