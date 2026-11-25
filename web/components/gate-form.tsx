"use client";

import { useActionState, useState } from "react";
import { CircleAlert, ShieldCheck } from "lucide-react";

import { submitGate } from "@/app/actions";
import { Button } from "@/components/ui/button";
import { FieldHint, Input, Label, Textarea } from "@/components/ui/field";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import type { ActionState } from "@/lib/types";

interface WarningRow {
  rule_id: string;
  title: string;
  message: string;
  justified: boolean;
}

const DECISIONS = [
  {
    value: "aprobar",
    label: "Habilitar para consulta",
    hint: "Publica el agregado en la consulta pública con su recibo.",
  },
  {
    value: "rechazar",
    label: "Rechazar",
    hint: "No se publica. Si ya estaba publicado, se retira del portal.",
  },
];

export function GateForm({
  caseId,
  blocking,
  warnings,
}: {
  caseId: string;
  blocking: string[];
  warnings: WarningRow[];
}) {
  const [state, formAction, pending] = useActionState<ActionState, FormData>(submitGate, {
    ok: true,
  });
  const blocked = blocking.length > 0;
  const [decision, setDecision] = useState(blocked ? "rechazar" : "aprobar");
  const [rationale, setRationale] = useState("");

  const pendingWarnings = warnings.filter((warning) => !warning.justified);
  const selected = DECISIONS.find((item) => item.value === decision);

  return (
    <div className="space-y-4">
      {blocked ? (
        <div className="rounded-lg border border-[#e7bdb9] bg-fail-bg px-4 py-3 text-[13px] text-fail">
          <p className="flex items-center gap-1.5 font-semibold">
            <CircleAlert className="h-4 w-4" aria-hidden />
            No habilitable todavía
          </p>
          <ul className="mt-1.5 list-disc space-y-0.5 pl-5">
            {blocking.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
          <p className="mt-2 text-[12px]">
            El bloqueo lo imponen las reglas y el estado del recurso, no la interfaz.
          </p>
        </div>
      ) : null}

      <form action={formAction} className="space-y-4">
        <input type="hidden" name="case_id" value={caseId} />
        <input type="hidden" name="decision" value={decision} />

        {!blocked && warnings.length ? (
          <div className="space-y-3">
            <div>
              <p className="text-[13px] font-semibold text-ink">Advertencias por justificar</p>
              <p className="text-[12px] text-muted">
                Cada advertencia necesita dueño y motivo antes de habilitar el agregado.
              </p>
            </div>
            {warnings.map((warning) => (
              <div
                key={warning.rule_id}
                className="rounded-lg border border-[#ecd3a1] bg-[#fffaf0] p-3"
              >
                <p className="mb-1 flex flex-wrap items-center gap-2 text-[11.5px] text-warn">
                  <span className="font-mono">{warning.rule_id}</span>
                  {warning.justified ? (
                    <span className="rounded-full bg-ok-bg px-2 py-0.5 text-[10.5px] font-semibold text-ok">
                      justificada
                    </span>
                  ) : null}
                </p>
                <p className="mb-2 text-[13px] leading-relaxed text-ink">{warning.message}</p>
                {warning.justified ? null : (
                  <div className="grid gap-2 sm:grid-cols-2">
                    <div>
                      <Label htmlFor={`just_owner__${warning.rule_id}`}>Dueño / responsable</Label>
                      <Input
                        id={`just_owner__${warning.rule_id}`}
                        name={`just_owner__${warning.rule_id}`}
                        required
                        placeholder="Quién responde"
                      />
                    </div>
                    <div>
                      <Label htmlFor={`just_policy__${warning.rule_id}`}>
                        Referencia de política
                      </Label>
                      <Input
                        id={`just_policy__${warning.rule_id}`}
                        name={`just_policy__${warning.rule_id}`}
                        placeholder="POL-2026-01 (opcional)"
                      />
                    </div>
                    <div className="sm:col-span-2">
                      <Label htmlFor={`just_reason__${warning.rule_id}`}>
                        Motivo de la excepción
                      </Label>
                      <Textarea
                        id={`just_reason__${warning.rule_id}`}
                        name={`just_reason__${warning.rule_id}`}
                        required
                        className="min-h-[64px]"
                        placeholder="Por qué se acepta esta advertencia"
                      />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : null}

        <div>
          <Label htmlFor="operator">Responsable del gate</Label>
          <Input
            id="operator"
            name="operator"
            required
            placeholder="Nombre y rol"
            autoComplete="name"
          />
        </div>

        <div>
          <Label htmlFor="decision-trigger">Decisión</Label>
          <Select value={decision} onValueChange={setDecision}>
            <SelectTrigger id="decision-trigger">
              <SelectValue>{selected?.label}</SelectValue>
            </SelectTrigger>
            <SelectContent>
              {DECISIONS.filter((item) => !blocked || item.value === "rechazar").map((item) => (
                <SelectItem key={item.value} value={item.value}>
                  {item.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <FieldHint>{selected?.hint}</FieldHint>
        </div>

        <div>
          <div className="flex items-center justify-between">
            <Label htmlFor="rationale">Motivo de la decisión</Label>
            <span
              className={cn(
                "text-[11px]",
                rationale.trim().length >= 10 ? "text-ok" : "text-muted",
              )}
            >
              {rationale.trim().length >= 10
                ? "mínimo alcanzado"
                : `${rationale.trim().length}/10 caracteres`}
            </span>
          </div>
          <Textarea
            id="rationale"
            name="rationale"
            required
            minLength={10}
            value={rationale}
            onChange={(event) => setRationale(event.target.value)}
            placeholder="Qué se cotejó y por qué se habilita o se rechaza"
          />
        </div>

        {state.message ? (
          <p
            className={cn(
              "rounded-md border px-3 py-2 text-[13px]",
              state.ok
                ? "border-[#b9dcc7] bg-ok-bg text-ok"
                : "border-[#e7bdb9] bg-fail-bg text-fail",
            )}
          >
            {state.message}
          </p>
        ) : null}

        <Button
          type="submit"
          variant={decision === "rechazar" ? "danger" : "default"}
          disabled={pending || (blocked && decision !== "rechazar")}
          className="w-full"
        >
          {decision === "rechazar" ? (
            pending ? (
              "Registrando rechazo…"
            ) : (
              "Registrar rechazo"
            )
          ) : (
            <>
              <ShieldCheck className="h-4 w-4" aria-hidden />
              {pending ? "Registrando decisión…" : "Registrar decisión"}
            </>
          )}
        </Button>
        <p className="text-center text-[11.5px] text-muted">
          La decisión queda ligada al digest de validación y se registra en el recibo.
        </p>
      </form>
    </div>
  );
}
