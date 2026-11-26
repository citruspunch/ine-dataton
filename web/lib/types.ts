export type StateName =
  | "borrador"
  | "no_habilitado"
  | "en_revision"
  | "habilitado_para_consulta"
  | "cerrado";

export type Severity = "ok" | "advertencia" | "falla" | "no_evaluado";

export interface Finding {
  rule_id: string;
  title: string;
  status: Severity;
  critical: boolean;
  message: string;
  evidence: Record<string, unknown>;
  justified: boolean;
}

export interface VariablesSummary {
  row_count: number;
  coverage?: {
    period?: string | null;
    notes?: string | null;
  };
  columns: {
    name: string;
    column: string;
    type: string;
    unit: string | null;
    reference: string | null;
    nullable: boolean;
    notes: string | null;
    present: boolean;
    valid_count: number | null;
    null_count: number | null;
    excluded_count: number | null;
  }[];
}

export interface Entity {
  kind: string;
  title?: string | null;
  dataset_id?: string | null;
  resource_id?: string | null;
  source_url?: string | null;
  downloaded_at_utc?: string | null;
  sha256?: string | null;
  bytes?: number | null;
  origin?: string;
  topic?: string | null;
  profile: string;
  license: {
    id?: string | null;
    verified?: boolean;
    attribution?: string | null;
    evidence?: string | null;
  };
  display: { period?: string; base?: string; unit?: string };
  variables_summary?: VariablesSummary | null;
  resources?: { manifest_item: string; identity: Record<string, string> }[];
  same_bytes?: boolean;
}

export interface Coverage {
  rules_total: number;
  critical_total: number;
  critical_evaluated: number;
  critical_not_evaluated: number;
  complete: boolean;
  by_status: Record<string, number>;
}

export interface Decision {
  decision_id: string;
  case_id: string;
  decided_at_utc: string;
  operator: string;
  rationale: string;
  gate_decision: string;
  decision_basis_digest: string;
  justifications?: Record<string, { owner?: string; reason?: string }>;
}

export interface ReviewPayload {
  case_id: string;
  label: string;
  method: string;
  entity: Entity;
  state: StateName;
  state_text: string;
  coverage: Coverage;
  digest: string;
  findings: Finding[];
  blocking: string[];
  warnings: { rule_id: string; title: string; message: string; justified: boolean }[];
  decision: Decision | null;
  override: boolean;
  published: boolean;
}

export interface CaseRow {
  id: string;
  label: string;
  state: StateName;
  state_text: string;
  profile: string;
  origin: string;
  critical: string;
  override: boolean;
}

export interface ProfileDefinition {
  profile_id: string;
  yaml: string;
  data: Record<string, unknown> | null;
}

export interface ProfileSummary {
  profile_id: string;
  version: string;
  kind: string;
  kind_label: string;
  topic: string | null;
  title: string;
  description: string;
  expected_sheet: string | null;
  valid: boolean;
  errors: { field: string; message: string }[];
}

export interface AggregateSummary {
  case_id: string;
  label: string;
  title: string;
  state: StateName;
  state_text: string;
  digest: string;
  synthetic: boolean;
  origin: string;
  period: string | null;
  topic: string | null;
  variables_count: number;
  sha256: string | null;
}

export interface AggregateDetail {
  case_id: string;
  label: string;
  entity: Entity;
  state: StateName;
  state_text: string;
  coverage: Coverage;
  digest: string;
  findings: Finding[];
  published_at_utc: string;
  notice: string;
}

export interface Receipt {
  receipt_id: string;
  generated_at_utc: string;
  technical_payload: Record<string, unknown>;
  decision_log: Record<string, unknown> | null;
}

export interface ActionState {
  ok: boolean;
  message?: string;
  errors?: { field: string; message: string }[];
  profileId?: string;
}
