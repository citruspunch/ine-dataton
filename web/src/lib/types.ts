export type PressureClass = "alta" | "media_alta" | "media" | "baja" | "sin_dato";
export type IndicatorFormat =
  | "percent"
  | "ratio"
  | "currency"
  | "integer"
  | "index";

export interface PressureScore {
  percentil: number | null;
  rank_nacional: number | null;
  rank_departamento: number | null;
  clase: PressureClass | null;
}

export interface Municipality {
  municipio_codigo: string;
  municipio_nombre: string;
  departamento_codigo: string;
  departamento_nombre: string;
  poblacion_2015: number | null;
  poblacion_2025: number | null;
  poblacion_2030: number | null;
  poblacion_2030_ckan: number | null;
  poblacion_2035: number | null;
  crecimiento_abs_2025_2035: number | null;
  crecimiento_poblacional_pct: number | null;
  crecimiento_poblacional_pct_2015_2025: number | null;
  nacimientos_2025: number | null;
  defunciones_2025: number | null;
  defunciones_menores_5_2025: number | null;
  nacimientos_por_1000_habitantes_2025: number | null;
  tasa_mortalidad_general_2025: number | null;
  tasa_mortalidad_menor_5_2025: number | null;
  relacion_nacimientos_defunciones_2025: number | null;
  escuelas_2022: number | null;
  escuelas_publicas_2022: number | null;
  estudiantes_2022: number | null;
  estudiantes_publicos_2022: number | null;
  nacimientos_por_escuela_2025: number | null;
  estudiantes_por_escuela_2022: number | null;
  nacimientos_por_100_estudiantes_2025: number | null;
  escuelas_por_10000_habitantes_2022: number | null;
  estudiantes_por_10000_habitantes_2022: number | null;
  pobreza_general_pct_2023: number | null;
  pobreza_extrema_pct_2023: number | null;
  poblacion_en_pobreza_2023: number | null;
  poblacion_en_pobreza_extrema_2023: number | null;
  brecha_pobreza_general_2023: number | null;
  severidad_pobreza_general_2023: number | null;
  consumo_promedio_q_mes_2023: number | null;
  asignacion_constitucional_2026_gtq: number | null;
  poblacion_asignacion_2025: number | null;
  asignacion_por_habitante_2026_gtq: number | null;
  asignacion_presion_indice_2026: number | null;
  ingresos_propios_2024_gtq: number | null;
  ingresos_propios_per_capita_2024_gtq: number | null;
  aldeas_caserios_2025: number | null;
  campos_suprimidos: string[];
  tiene_supresion: boolean;
  presion: Record<string, PressureScore>;
}

export interface LicenseInfo {
  id: string;
  name: string;
  url: string | null;
  commercial_use: boolean | null;
  attribution_required: boolean;
  ckan_license_id: string | null;
  ckan_license_title: string | null;
  status: string;
  notes: string;
}

export interface SourceRecord {
  id: string;
  title: string;
  publisher: string;
  dataset_page: string;
  download_url: string;
  filename: string;
  format: string;
  license: LicenseInfo;
  attribution: string;
  description: string;
  verified_on: string;
  downloaded_at_utc: string | null;
  download_status: string | null;
  sha256: string | null;
  bytes: number | null;
  http_status: number | null;
  content_type: string | null;
  local_path: string | null;
  license_status: string;
  ckan_license_id: string | null;
  non_commercial: boolean;
  license_notice: string;
}

export interface IndicatorSourceMetadata {
  id: string;
  title: string;
  license: LicenseInfo;
  downloaded_at_utc: string | null;
  download_url: string;
}

export interface IndicatorDefinition {
  key: string;
  label: string;
  short_label: string;
  unit: string;
  format: IndicatorFormat;
  direction: "higher" | "lower" | null;
  rank: boolean;
  sources: string[];
  license_summary: string;
  description: string;
  source_metadata: IndicatorSourceMetadata[];
}

export interface Department {
  codigo: string;
  nombre: string;
  municipios: number;
  poblacion_2025: number;
  nacimientos_2025: number;
  escuelas_2022: number;
  estudiantes_2022: number;
  asignacion_constitucional_2026_gtq: number;
  pobreza_general_pct_2023: number | null;
}

export interface Highlight {
  codigo: string;
  municipio: string;
  departamento: string;
  valor: number;
  clase: PressureClass | null;
}

export interface SuppressionPayload {
  threshold: number;
  ui_label: string;
  legal_basis: string;
  counts: {
    threshold: number;
    rule: string;
    count_fields: Array<{
      field: string;
      label: string;
      suppressed_cells: number;
    }>;
    suppressed_cells_by_field: Record<string, number>;
    suppressed_cells_total: number;
    municipalities_with_suppression: number;
    legal_basis: string;
    notes: string;
  };
  derived: {
    derived_fields: Array<{
      field: string;
      label: string;
      suppressed_cells: number;
    }>;
    suppressed_cells_total: number;
  };
  total_suppressed_cells: number;
  labels: Record<string, string>;
}

export interface IndicatorsPayload {
  snapshot_id: string;
  generated_at_utc: string;
  verified_on: string;
  title: string;
  subtitle: string;
  disclaimer: string;
  ai_disclosure: string;
  municipality_count: number;
  department_count: number;
  indicators: IndicatorDefinition[];
  pressure_indicator_keys: string[];
  pressure_class_labels: Record<PressureClass, string>;
  departments: Department[];
  municipalities: Municipality[];
  summary: {
    national_totals: {
      poblacion_2025: number;
      poblacion_2035: number;
      nacimientos_2025: number;
      defunciones_2025: number;
      escuelas_2022: number;
      estudiantes_2022: number;
      asignacion_constitucional_2026_gtq: number;
    };
    pressure_classes: Record<string, Record<string, number>>;
    national_per_capita_allocation_2026_gtq: number;
    municipalities_with_complete_pressure: number;
    highlights: Record<string, Highlight[]>;
  };
  suppression: SuppressionPayload;
  data_quality: {
    municipality_count: number;
    department_count: number;
    join_status: string;
    crosswalk: {
      rows: number;
      crosswalk_applied: number;
      crosswalk_mapping: string;
    };
    projection_overlap: {
      rows_compared: number;
      max_abs_difference_people: number;
      max_abs_difference_year: number;
      tolerance_people: number;
      status: string;
    };
    reference_catalog: {
      rows: number;
      departments: number;
      coding_note: string;
    };
    mineduc_2022: {
      establishments: {
        total_schools: number;
        min_schools: number;
        max_schools: number;
        year: string;
        counting_rule: string;
      };
      students: {
        total_students: number;
        min_students: number;
        max_students: number;
        year: string;
        counting_rule: string;
      };
    };
    vital_events_2025: {
      births: {
        rows_used: number;
        rows_unmatched: number;
        unmatched_codes: Array<{ codigo: string; registros: number }>;
        residence_field: string;
        min_count: number;
        max_count: number;
      };
      deaths: {
        rows_used: number;
        rows_unmatched: number;
        under5_total: number;
        under5_small_count_candidates: number;
        residence_field: string;
      };
    };
    segeplan: {
      poverty_2023: {
        rows: number;
        missing_extreme_poverty: number;
        year: number;
      };
      allocation_2026: {
        rows: number;
        total_allocation_gtq: number;
        national_per_capita_gtq: number;
        year: number;
        notes: string;
      };
    };
  };
  sources: SourceRecord[];
  limitations: string[];
}
