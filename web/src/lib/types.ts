export type ViewId = "2024" | "series";

export interface Notice {
  id: string;
  label: string;
  severity: "warning" | "info";
  badges: string[];
  title: string;
  body: string;
  footnote: string;
}

export interface ViewConfig {
  id: ViewId;
  label: string;
  label_es: string;
  short_label: string;
  dinese_years: number[];
  total_establishments: number | Record<string, number>;
  legal_categories: number | Record<string, number>;
  notice: Notice;
}

export interface CiiuSection {
  letter: string;
  name: string;
  short: string;
}

export interface DinesePayload {
  year?: number;
  total: number;
  ciiu: Record<string, number>;
  size: Record<string, number>;
  legal: Record<string, number>;
  legal_order?: string[];
}

export interface AgeGroup {
  label: string;
  count: number;
}

export interface Population {
  total: number;
  men: number;
  women: number;
  urban: number;
  rural: number;
  age_groups: AgeGroup[];
  age_summary: {
    under_15: number;
    working_age: number;
    over_64: number;
    under_15_share: number | null;
    working_age_share: number | null;
    over_64_share: number | null;
    urban_share: number | null;
  };
}

export interface Place {
  code: string;
  name: string;
  lon: number | null;
  lat: number | null;
  excluded: boolean;
  reasons: string[];
}

export interface Places {
  total: number;
  map_points: number;
  excluded: {
    suffix_999: number;
    missing_coordinates: number;
    union: number;
    both: number;
  };
  items: Place[];
}

export interface Profile {
  code: string;
  name: string;
  department_code: string;
  department_name: string;
  population: Population;
  snapshot_2024: DinesePayload;
  series_2021_2022: {
    years: [number, number];
    2021: DinesePayload;
    2022: DinesePayload;
  };
  places: Places;
}

export interface Municipality {
  code: string;
  name: string;
  department_code: string;
  department_name: string;
  population: number;
  establishments: Record<string, number>;
  ranks: Record<string, number>;
}

export interface Department {
  code: string;
  name: string;
  municipality_count: number;
}

export interface SourceEntry {
  key: string;
  filename: string;
  dataset: string;
  title: string;
  year: number;
  kind: string;
  url: string;
  page_url: string;
  bytes: number;
  sha256: string;
  status: string;
  downloaded_at_utc: string;
  last_verified_utc: string;
  license: {
    id: string;
    title: string;
    url: string;
    status: string;
  };
}

export interface Meta {
  schema_version: number;
  generated_at_utc: string;
  pipeline_version: string;
  title: string;
  subtitle: string;
  census_year: number;
  views: ViewConfig[];
  notices: Record<ViewId, Notice>;
  ciiu_sections: CiiuSection[];
  size_order: string[];
  legal_categories: Record<string, string[]>;
  legal_short_labels: Record<string, string>;
  national: {
    population: {
      total: number;
      men: number;
      women: number;
      urban: number;
      rural: number;
      age_groups: AgeGroup[];
    };
    dinese: Record<string, DinesePayload>;
  };
  coverage: {
    municipalities: number;
    departments: number;
    crosswalk: string;
    dinese_pairs: Record<string, string>;
    dinese_records: Record<string, number>;
    dinese_ciiu_sections: number;
    places_total: number;
    places_map_points: number;
    places_excluded_suffix_999: number;
    places_excluded_missing_coordinates: number;
    places_excluded_union: number;
  };
  sources: SourceEntry[];
  limitations: string[];
  definitions: Record<string, string>;
}

export interface MunicipalitiesPayload {
  generated_at_utc: string;
  departments: Department[];
  municipalities: Municipality[];
}
