import type {
  CountFacet,
  GroupSummary,
  MetricStats,
  QualitySummary,
  QueryParams,
  QueryResult,
  RecordItem,
  SourceGroup,
  Summary,
  UnitGroup,
} from "./types";

export function normalizeText(value: string | null | undefined): string {
  return (value ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

export function defaultMetricForSource(source: SourceGroup): string {
  switch (source) {
    case "DPIR":
      return "Precio de referencia";
    case "IPMC":
      return "Índice IPMC";
    case "ICC":
      return "Índice ICC";
    case "BASKETS":
      return "Costo mensual per cápita";
  }
}

export function unitOf(record: RecordItem): string {
  if (record.valueKind === "index" || record.valueKind === "cost") {
    return record.metricUnit ?? record.unit ?? "Sin unidad";
  }
  return record.unit ?? record.metricUnit ?? "Sin unidad";
}

export function isProblematicRecord(record: RecordItem): boolean {
  return record.flags.some((flag) =>
    ["invalid_date", "missing_date", "duplicate", "missing_value", "missing_product"].includes(
      flag,
    ),
  );
}

function startOf(value: string | undefined): string | null {
  if (!value) return null;
  if (/^\d{4}-\d{2}$/.test(value)) return `${value}-01`;
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return value;
  return null;
}

function endOf(value: string | undefined): string | null {
  if (!value) return null;
  if (/^\d{4}-\d{2}$/.test(value)) {
    const [year, month] = value.split("-").map(Number);
    const day = new Date(Date.UTC(year, month, 0)).getUTCDate();
    return `${value}-${String(day).padStart(2, "0")}`;
  }
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return value;
  return null;
}

function percentile(values: number[], fraction: number): number {
  if (values.length === 0) return 0;
  if (values.length === 1) return values[0];
  const position = (values.length - 1) * fraction;
  const low = Math.floor(position);
  const high = Math.ceil(position);
  if (low === high) return values[low];
  const weight = position - low;
  return values[low] * (1 - weight) + values[high] * weight;
}

function baseSummary(items: RecordItem[]) {
  const values = items
    .map((item) => item.value)
    .filter((value): value is number => value !== null)
    .sort((a, b) => a - b);
  const dates = items
    .map((item) => item.date)
    .filter((date): date is string => Boolean(date))
    .sort();
  if (values.length === 0) return null;
  return {
    count: values.length,
    min: values[0],
    p25: percentile(values, 0.25),
    median: percentile(values, 0.5),
    p75: percentile(values, 0.75),
    max: values[values.length - 1],
    mean: values.reduce((sum, value) => sum + value, 0) / values.length,
    cutoff: dates.length ? dates[dates.length - 1] : null,
  };
}

function overallUnit(
  metric: string,
  valueKind: string,
  unitGroups: UnitGroup[],
  metricUnit: string | null,
): string {
  if (metric === "Precio de referencia") return "Q (todas las presentaciones)";
  if (metric === "Precio por unidad base") return "Q por unidad base (presentaciones distintas)";
  if (metricUnit) return metricUnit;
  return unitGroups[0]?.unit ?? "—";
}

export function computeStats(records: RecordItem[]): MetricStats[] {
  const canonical = records.filter(
    (record) =>
      !record.flags.includes("duplicate") && record.value !== null && record.date !== null,
  );
  const byMetric = new Map<string, RecordItem[]>();
  for (const record of canonical) {
    const list = byMetric.get(record.metric) ?? [];
    list.push(record);
    byMetric.set(record.metric, list);
  }

  const output: MetricStats[] = [];
  for (const [metric, items] of byMetric) {
    const overall = baseSummary(items);
    if (!overall) continue;

    const byUnit = new Map<string, RecordItem[]>();
    for (const record of items) {
      const key = normalizeText(unitOf(record));
      const list = byUnit.get(key) ?? [];
      list.push(record);
      byUnit.set(key, list);
    }
    const unitGroups: UnitGroup[] = [];
    for (const unitItems of byUnit.values()) {
      const summary = baseSummary(unitItems);
      if (!summary) continue;
      const units = new Map<string, number>();
      for (const item of unitItems) {
        const unit = unitOf(item);
        units.set(unit, (units.get(unit) ?? 0) + 1);
      }
      const displayUnit = [...units.entries()].sort((a, b) => b[1] - a[1])[0][0];
      unitGroups.push({ key: normalizeText(displayUnit), unit: displayUnit, ...summary });
    }
    unitGroups.sort((a, b) => b.count - a.count || a.unit.localeCompare(b.unit, "es"));

    output.push({
      key: metric
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-+|-+$/g, ""),
      metric,
      unit: overallUnit(metric, items[0].valueKind, unitGroups, items[0].metricUnit),
      valueKind: items[0].valueKind,
      currency: items[0].currency,
      ...overall,
      unitGroups,
      sources: [...new Set(items.map((item) => item.source))].sort(),
      levels: [...new Set(items.map((item) => item.level).filter((level): level is string => Boolean(level)))].sort(),
    });
  }

  output.sort((a, b) => b.count - a.count || a.metric.localeCompare(b.metric, "es"));
  return output;
}

function qualitySummary(records: RecordItem[]): QualitySummary {
  const flags = new Map<string, number>();
  let canonical = 0;
  for (const record of records) {
    for (const flag of record.flags) flags.set(flag, (flags.get(flag) ?? 0) + 1);
    if (!record.flags.includes("duplicate") && record.value !== null && record.date !== null) {
      canonical += 1;
    }
  }
  return {
    totalRecords: records.length,
    canonicalRecords: canonical,
    excludedFromStats: records.length - canonical,
    invalidDate: flags.get("invalid_date") ?? 0,
    missingDate: flags.get("missing_date") ?? 0,
    duplicates: flags.get("duplicate") ?? 0,
    thousandsComma: flags.get("thousands_comma") ?? 0,
    missingNog: flags.get("missing_nog") ?? 0,
    missingValue: flags.get("missing_value") ?? 0,
    missingProduct: flags.get("missing_product") ?? 0,
  };
}

function metricFacets(records: RecordItem[]): CountFacet[] {
  const counts = new Map<string, number>();
  for (const record of records) counts.set(record.metric, (counts.get(record.metric) ?? 0) + 1);
  return [...counts.entries()]
    .map(([value, count]) => ({ value, label: value, count }))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, "es"));
}

function unitFacets(records: RecordItem[]): CountFacet[] {
  const counts = new Map<string, { label: string; count: number }>();
  for (const record of records) {
    const unit = unitOf(record);
    const key = normalizeText(unit);
    const entry = counts.get(key) ?? { label: unit, count: 0 };
    entry.count += 1;
    counts.set(key, entry);
  }
  return [...counts.entries()]
    .map(([value, entry]) => ({ value, label: entry.label, count: entry.count }))
    .sort((a, b) => b.count - a.count || a.label.localeCompare(b.label, "es"));
}

function groupSummary(summary: Summary, source: SourceGroup): GroupSummary {
  return summary.groups[source] ?? summary.groups.DPIR;
}

export function queryRecords(
  allRecords: RecordItem[],
  summary: Summary,
  params: QueryParams,
): QueryResult {
  const source = params.source;
  const query = normalizeText(params.q);
  const tokens = query ? query.split(" ").filter(Boolean) : [];
  const from = startOf(params.from);
  const to = endOf(params.to);
  const pageSize = Math.max(1, Math.min(100, params.pageSize ?? 25));

  const base = allRecords.filter((record) => {
    if (record.sourceGroup !== source) return false;
    if (tokens.length && !tokens.every((token) => record.s.includes(token))) return false;
    if (from || to) {
      if (!record.date) return false;
      if (from && record.date < from) return false;
      if (to && record.date > to) return false;
    }
    return true;
  });

  const statsByMetric = computeStats(base);
  const availableMetrics = statsByMetric.map((stats) => stats.metric);
  const requestedMetric = params.metric && availableMetrics.includes(params.metric)
    ? params.metric
    : null;
  const defaultMetric = defaultMetricForSource(source);
  const selectedMetric =
    requestedMetric ??
    (availableMetrics.includes(defaultMetric) ? defaultMetric : availableMetrics[0] ?? null);

  const metricRecords = selectedMetric
    ? base.filter((record) => record.metric === selectedMetric)
    : base;

  const units = unitFacets(metricRecords);
  const requestedUnit = params.unit ? normalizeText(params.unit) : null;
  const selectedUnit = requestedUnit && units.some((unit) => unit.value === requestedUnit)
    ? units.find((unit) => unit.value === requestedUnit)?.label ?? null
    : null;

  const unitRecords = selectedUnit
    ? metricRecords.filter((record) => normalizeText(unitOf(record)) === normalizeText(selectedUnit))
    : metricRecords;

  const filteredStats = computeStats(unitRecords);
  const stats =
    filteredStats.find((entry) => entry.metric === selectedMetric) ??
    filteredStats[0] ??
    null;

  const tableBase = params.includeAlerts
    ? unitRecords
    : unitRecords.filter((record) => !isProblematicRecord(record));
  const sorted = [...tableBase].sort((a, b) => {
    if (a.date && b.date && a.date !== b.date) return b.date.localeCompare(a.date);
    if (a.date && !b.date) return -1;
    if (!a.date && b.date) return 1;
    const aDuplicate = a.flags.includes("duplicate");
    const bDuplicate = b.flags.includes("duplicate");
    if (aDuplicate !== bDuplicate) return aDuplicate ? 1 : -1;
    return a.item.localeCompare(b.item, "es");
  });

  const total = sorted.length;
  const pageCount = Math.max(1, Math.ceil(total / pageSize));
  const page = Math.max(1, Math.min(params.page ?? 1, pageCount));
  const records = sorted.slice((page - 1) * pageSize, page * pageSize);

  return {
    records,
    total,
    page,
    pageSize,
    pageCount,
    stats,
    statsByMetric: filteredStats.length ? filteredStats : statsByMetric,
    selectedMetric,
    selectedUnit,
    facets: {
      metrics: metricFacets(base),
      units,
    },
    quality: qualitySummary(unitRecords),
    cutoff: stats?.cutoff ?? null,
    group: groupSummary(summary, source),
    query: { ...params, source, page, pageSize, metric: selectedMetric ?? undefined, unit: selectedUnit ?? undefined },
  };
}
