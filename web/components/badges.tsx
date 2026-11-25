import { Badge } from "@/components/ui/badge";
import type { Severity, StateName } from "@/lib/types";

const STATE_VARIANT: Record<StateName, "ok" | "warn" | "fail" | "none"> = {
  habilitado_para_consulta: "ok",
  en_revision: "warn",
  no_habilitado: "fail",
  cerrado: "none",
  borrador: "none",
};

const SEVERITY_VARIANT: Record<Severity, "ok" | "warn" | "fail" | "none"> = {
  ok: "ok",
  advertencia: "warn",
  falla: "fail",
  no_evaluado: "none",
};

export function StateBadge({ state, text }: { state: StateName; text: string }) {
  return <Badge variant={STATE_VARIANT[state] ?? "none"}>{text}</Badge>;
}

export function SeverityBadge({ status }: { status: Severity }) {
  return <Badge variant={SEVERITY_VARIANT[status] ?? "none"}>{status}</Badge>;
}
