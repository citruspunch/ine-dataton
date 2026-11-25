export type Area = "Urbana" | "Rural";
export type Mode = "total" | "kcal";
export type VariationType = "monthly" | "interannual";

/** [precio por unidad base, kcal por persona/día, costo por persona/día, Q por 1.000 kcal] */
export type ProductValues = [number, number, number, number | null];

/** [costo por persona/día, kcal por persona/día, Q por 1.000 kcal, % del gasto] */
export type GroupValues = [number, number, number, number | null];

export type ProductCatalogItem = {
  name: string;
  group: string;
  baseQuantity: number;
  baseUnit: string;
  zeroKcal: boolean;
};

export type AreaMonth = {
  period: string;
  year: number;
  month: number;
  monthName: string;
  label: string;
  dailyCostPerPerson: number;
  monthlyCostPerPerson: number;
  caloricCostPerPersonDay: number;
  excludedCostPerPersonDay: number;
  dailyKcalPerPerson: number;
  coveragePct: number;
  costPerThousandKcal: number;
  productValues: ProductValues[];
  groupValues: GroupValues[];
};

export type AreaData = {
  products: ProductCatalogItem[];
  groups: string[];
  months: AreaMonth[];
};

export type IpcRow = {
  period: string;
  year: number;
  month: number;
  monthName: string;
  officialMonthly: number;
  officialInterannual: number;
  officialAccumulated: number;
  directMonthly: number | null;
  directInterannual: number | null;
  crossBaseMonthly: boolean;
  crossBaseInterannual: boolean;
  directMonthlyGapPp: number | null;
  directInterannualGapPp: number | null;
  publishedIndex: number | null;
  publishedBase: string;
  officialIndexDec2023: number;
  officialIndex2024: number;
};

export type AreaSummary = {
  area: Area;
  referenceKcal: number;
  productCount: number;
  groupCount: number;
  zeroKcalProducts: string[];
  period: { first: string; last: string; count: number };
};

export type SourceEntry = {
  key: string;
  filename: string;
  local_path: string;
  title: string;
  role: string;
  coverage: string;
  source_url: string;
  retrieved_from: "download" | "local-cache" | "local-file";
  downloaded_at_utc: string | null;
  verified_at_utc: string;
  bytes: number;
  sha256: string;
  license: {
    status: "declarada" | "no declarada";
    id: string | null;
    title: string;
    url: string | null;
  };
  ckan: {
    portal: string;
    package_id: string;
    package_name: string;
    package_title: string;
    package_url: string;
    resource_id: string;
    resource_last_modified_utc: string;
  };
  notes: string;
};

export type BasketMeta = {
  generatedAtUtc: string;
  generator: string;
  period: {
    first: string;
    last: string;
    count: number;
    firstLabel: string;
    lastLabel: string;
  };
  daysPerMonth: number;
  areas: Record<Area, AreaSummary>;
  checks: Record<
    Area,
    {
      periods: number;
      products: number;
      groups: number;
      kcalPerDay: number;
      maxGroupCostGapQ: number;
      zeroKcalProducts: string[];
    }
  >;
  splice: {
    baseBreakPeriod: string;
    linkFactor2023To2024: number;
    dec2024IndexDec2023Base: number;
    jan2025Index2024Base: number;
    officialJan2025Monthly: number;
    directJan2025Monthly: number;
  };
  sources: SourceEntry[];
};

export type BasketData = {
  meta: BasketMeta;
  areas: Record<Area, AreaData>;
  ipc: IpcRow[];
};

export type ProductRow = {
  name: string;
  group: string;
  baseQuantity: number;
  baseUnit: string;
  zeroKcal: boolean;
  unitPrice: number;
  kcalPerPersonDay: number;
  costPerPersonDay: number;
  costPerPersonMonth: number;
  costPerThousandKcal: number | null;
};

export type GroupRow = {
  name: string;
  shortName: string;
  costPerPersonDay: number;
  costHouseholdMonth: number;
  kcalPerPersonDay: number;
  costPerThousandKcal: number;
  sharePct: number;
};

export type TrendPoint = {
  period: string;
  label: string;
  shortLabel: string;
  value: number;
};
