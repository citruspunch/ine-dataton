import { PriceDesk } from "@/components/price-desk";
import { loadCatalog, loadRecords, loadSummary } from "@/lib/data";
import { queryRecords } from "@/lib/query";

export default function Home() {
  const summary = loadSummary();
  const catalog = loadCatalog();
  const records = loadRecords();
  const base = queryRecords(records, summary, {
    source: "DPIR",
    q: "computadora",
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
        q: "computadora",
        unit: initialUnit,
        page: 1,
        pageSize: 25,
      })
    : base;

  return <PriceDesk initial={initial} summary={summary} catalog={catalog} />;
}
