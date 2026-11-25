export type TopicId = "road_safety" | "births" | "deaths";
export type CriterionId = "residence" | "occurrence";
export type LevelId = "department" | "municipality";
export type Mode = "rate" | "count";

export type PublicCell = {
  suppressed: false;
  count: number;
  rate: number;
  threshold: number;
};

export type SuppressedCell = {
  suppressed: true;
  threshold: number;
};

export type Cell = PublicCell | SuppressedCell;

export type CountCell =
  | { suppressed: false; count: number; threshold: number }
  | SuppressedCell;

export type LevelCells = {
  cells: Record<string, Cell>;
  suppressed_territories: number;
  published_territories: number;
  total_count: number;
};

export type AvailableCriterion = {
  available: true;
  note: string;
  threshold: number;
  national: Cell;
  levels: Record<LevelId, LevelCells>;
};

export type UnavailableCriterion = {
  available: false;
  reason: string;
};

export type Criterion = AvailableCriterion | UnavailableCriterion;

export type Metric = {
  id: string;
  label: string;
  unit: string;
  description: string;
  criteria: Record<CriterionId, Criterion>;
};

export type Topic = {
  label: string;
  shortLabel?: string;
  description: string;
  metrics: Record<string, Metric>;
  onlyOccurrence?: boolean;
};

export type Indicators = {
  generatedAtUtc: string;
  dataYear: number;
  rateBase: number;
  topics: Record<TopicId, Topic>;
};

export type Territory = {
  code: string;
  name: string;
  dept: string;
  deptName: string;
  population: number;
  census2018: number;
  lon: number | null;
  lat: number | null;
};

export type Department = {
  code: string;
  name: string;
  population: number;
  census2018: number;
  municipalities: number;
};

export type Territories = {
  departments: Department[];
  municipalities: Territory[];
};

export type CauseKey = "all" | "homicide" | "suicide" | "traffic";

export type CauseCriterion = {
  criterion: CriterionId;
  note: string;
  causes: Record<CauseKey, { label: string; threshold: number }>;
  national: Record<CauseKey, Cell>;
  levels: {
    department: {
      cells: Record<string, Record<CauseKey, Cell>>;
      suppressed_territories: Record<CauseKey, number>;
    };
    municipality: {
      cells: Record<string, Record<CauseKey, Cell>>;
      suppressed_territories: Record<CauseKey, number>;
    };
  };
};

export type DeathCauses = Record<CriterionId, CauseCriterion>;

export type AgeTopic = {
  label: string;
  criteria: Partial<
    Record<
      CriterionId,
      {
        national: CountCell[];
        departments: Record<string, CountCell[]>;
      }
    >
  >;
};

export type AgeProfile = {
  bands: string[];
  note: string;
  topics: Partial<Record<"births" | "deaths", AgeTopic>>;
};

export type PointTuple = [string, string, string, string, number, number];

export type Points = {
  fields: ["id", "name", "muni", "dept", "lon", "lat"];
  points: PointTuple[];
  filters: {
    source_places: number;
    excluded_suffix_999: number;
    excluded_missing_coordinates: number;
    excluded_unknown_territory: number;
    excluded_total: number;
    included: number;
    note: string;
  };
};

export type ProvenanceRow = {
  filename: string;
  url: string;
  kind: string;
  status: "cached" | "downloaded";
  origin: string;
  retrieved_at_utc: string;
  checked_at_utc: string;
  sha256: string;
  bytes: number;
  publisher: string;
  license: string;
};

export type Meta = {
  schemaVersion: number;
  title: string;
  subtitle: string;
  generatedAtUtc: string;
  dataYear: number;
  populationYear: number;
  rateBase: number;
  topics: Record<TopicId, { label: string; description: string }>;
  criteria: Record<CriterionId, string>;
  criterionNotes: Record<CriterionId, string>;
  thresholds: { general: number; homicideSuicide: number; rateBase: number };
  suppression: {
    law: string;
    general: number;
    homicideSuicide: number;
    text: string;
    smallCellPolicy: string;
  };
  population: {
    year: number;
    source: string;
    note: string;
    projectionHorizon: string;
    projectionNote: string;
  };
  pointLayer: Points["filters"];
  coverage: {
    municipalities: number;
    departments: number;
    crosswalk: string;
    diagnostics: Record<string, unknown>;
  };
  provenance: ProvenanceRow[];
  limits: string[];
  licenses: { name: string; detail: string; url?: string }[];
  aiDisclosure: string;
  methodology: Record<string, string>;
};

export type GeoFeatureProperties = {
  code: string;
  name: string;
  dept?: string;
  deptName?: string;
};

export type TerritoryGeo = {
  type: "FeatureCollection";
  features: {
    type: "Feature";
    properties: GeoFeatureProperties;
    geometry: { type: string; coordinates: unknown };
  }[];
};
