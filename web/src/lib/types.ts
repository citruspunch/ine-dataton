export type SourceGroup = "DPIR" | "IPMC" | "ICC" | "BASKETS";

export type ValueKind = "price" | "index" | "cost";

export interface RecordItem {
  id: string;
  source: string;
  sourceGroup: SourceGroup;
  dataset: string;
  item: string;
  category: string;
  metric: string;
  unit: string | null;
  metricUnit: string | null;
  value: number | null;
  valueKind: ValueKind;
  currency: string | null;
  date: string | null;
  dateRaw: string | null;
  dateStatus: "valid" | "invalid" | "missing";
  year: number | null;
  month: number | null;
  region: string | null;
  level: string | null;
  context: string | null;
  nog: string | null;
  description: string | null;
  status: "frozen" | "current" | "limited";
  flags: string[];
  duplicateOf?: string;
  s: string;
  dailyCost?: number | null;
  monthlyCost?: number | null;
  baseQuantity?: number | null;
  baseUnit?: string | null;
  materialNo?: number | null;
  baseValue?: number | null;
  indexBase?: string | null;
}

export interface UnitGroup {
  key: string;
  unit: string;
  count: number;
  min: number;
  p25: number;
  median: number;
  p75: number;
  max: number;
  mean: number;
  cutoff: string | null;
}

export interface MetricStats {
  key: string;
  metric: string;
  unit: string;
  valueKind: ValueKind;
  currency: string | null;
  count: number;
  min: number;
  p25: number;
  median: number;
  p75: number;
  max: number;
  mean: number;
  cutoff: string | null;
  unitGroups: UnitGroup[];
  sources: string[];
  levels: string[];
}

export interface QualitySummary {
  totalRecords: number;
  canonicalRecords: number;
  excludedFromStats: number;
  invalidDate: number;
  missingDate: number;
  duplicates: number;
  thousandsComma: number;
  missingNog: number;
  missingValue: number;
  missingProduct: number;
}

export interface CountedValue {
  value: string;
  count: number;
}

export interface GroupSummary {
  id: SourceGroup;
  label: string;
  shortLabel: string;
  tagline: string;
  description: string;
  status: "frozen" | "current" | "limited";
  statusLabel: string;
  cutoff: string | null;
  granularity: "day" | "month";
  recordCount: number;
  canonicalCount: number;
  flaggedCount: number;
  datasets: string[];
  metrics: MetricStats[];
  quality: QualitySummary;
  coverageNote: string;
  categories: CountedValue[];
  items: CountedValue[];
}

export interface Summary {
  generatedAt: string;
  groups: Record<SourceGroup, GroupSummary>;
  totalRecords: number;
  order: SourceGroup[];
}

export interface LicenseInfo {
  id: string;
  title: string;
  url: string | null;
}

export interface DatasetManifest {
  id: string;
  group: SourceGroup;
  title: string;
  fileName: string;
  url: string | null;
  attemptedUrls: Array<{
    url: string;
    status?: number;
    bytes?: number;
    ok?: boolean;
    reason?: string;
    error?: string;
  }>;
  sourcePage: string;
  publisher: string;
  downloadedAtUtc: string | null;
  verifiedAtUtc: string | null;
  retrieval: "download" | "local-cache" | null;
  sha256: string | null;
  bytes: number | null;
  httpStatus: number | null;
  contentType: string | null;
  ckanModified: string | null;
  license: LicenseInfo;
  status: "frozen" | "current" | "limited";
  coverage: string;
  notes: string;
  cutoff: string | null;
  recordCount: number;
  canonicalCount: number;
  isDictionary: boolean;
}

export interface DictionaryEntry {
  variable: string;
  description: string;
}

export interface Manifest {
  generatedAt: string;
  datasets: DatasetManifest[];
  dictionary: DictionaryEntry[];
  groupMeta: Record<
    SourceGroup,
    { label: string; shortLabel: string; tagline: string; description: string; statusLabel: string; accent: string }
  >;
  order: SourceGroup[];
  privacy: string;
  attribution: string;
  aiDisclosure: string;
}

export interface CatalogItem {
  value: string;
  category: string;
  metric: string;
  count: number;
}

export interface Catalog {
  [key: string]: {
    items: CatalogItem[];
    categories: CountedValue[];
  };
}

export interface CountFacet {
  value: string;
  label: string;
  count: number;
}

export interface QueryParams {
  source: SourceGroup;
  q?: string;
  from?: string;
  to?: string;
  metric?: string;
  unit?: string;
  includeAlerts?: boolean;
  page?: number;
  pageSize?: number;
}

export interface QueryResult {
  records: RecordItem[];
  total: number;
  page: number;
  pageSize: number;
  pageCount: number;
  stats: MetricStats | null;
  statsByMetric: MetricStats[];
  selectedMetric: string | null;
  selectedUnit: string | null;
  facets: {
    metrics: CountFacet[];
    units: CountFacet[];
  };
  quality: QualitySummary;
  cutoff: string | null;
  group: GroupSummary;
  query: QueryParams;
}
