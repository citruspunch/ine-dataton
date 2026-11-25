"use client";

import { useActionState } from "react";

import { submitGate } from "@/app/actions";
import { Button } from "@/components/ui/button";
import { Input, Label, Select, Textarea } from "@/components/ui/field";
import type { ActionState } from "@/lib/types";

interface WarningRow {
  rule_id: string;
  title: string;
  message: string;
  justified: boolean;
}

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

  return (
    <div className="space-y-3">
      {blocked ? (
        <>
          <p className="text-[15px] font-semibold">No habilitable todavía</p>
          <ul className="list-disc space-y-1 pl-5 text-[13px] text-muted">
            {blocking.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
          <p className="text-[13px] text-muted">
            El botón de habilitar queda bloqueado por las reglas, no por la interfaz.
          </p>
        </>
      ) : null}

      <form action={formAction} className="space-y-3">
        <input type="hidden" name="case_id" value={caseId} />

        {!blocked && warnings.length ? (
          <div className="space-y-3">
            <p className="text-[15px] font-semibold">Advertencias por justificar</p>
            {warnings.map((warning) => (
              <div
                key={warning.rule_id}
                className="rounded border border-line bg-[#fdfbf5] p-3"
              >
                <p className="mb-1 text-[12.5px] text-muted">
                  <span className="font-mono">{warning.rule_id}</span>
                  {warning.justified ? " · justificada" : ""}
                </p>
                <p className="mb-2 text-[13px]">{warning.message}</p>
                {warning.justified ? null : (
                  <>
                    <Label htmlFor={`just_owner__${warning.rule_id}`}>
                      Dueño / responsable
                    </Label>
                    <Input
                      id={`just_owner__${warning.rule_id}`}
                      name={`just_owner__${warning.rule_id}`}
                      required
                      placeholder="Quién responde"
                    />
                    <div className="h-2" />
                    <Label htmlFor={`just_reason__${warning.rule_id}`}>
                      Motivo de la excepción
                    </Label>
                    <Textarea
                      id={`just_reason__${warning.rule_id}`}
                      name={`just_reason__${warning.rule_id}`}
                      required
                      placeholder="Por qué se acepta esta advertencia"
                    />
                    <div className="h-2" />
                    <Label htmlFor={`just_policy__${warning.rule_id}`}>
                      Referencia de política (opcional)
                    </Label>
                    <Input
                      id={`just_policy__${warning.rule_id}`}
                      name={`just_policy__${warning.rule_id}`}
                      placeholder="POL-..."
                    />
                  </>
                )}
              </div>
            ))}
          </div>
        ) : null}

        <div>
          <Label htmlFor="operator">Responsable del gate</Label>
          <Input id="operator" name="operator" required placeholder="Nombre y rol" />
        </div>
        <div>
          <Label htmlFor="rationale">Motivo de la decisión</Label>
          <Textarea
            id="rationale"
            name="rationale"
            required
            minLength={10}
            placeholder="Qué se cotejó y por qué se habilita"
          />
        </div>
        <div>
          <Label htmlFor="decision">Decisión</Label>
          <Select id="decision" name="decision" defaultValue={blocked ? "rechazar" : "aprobar"}>
            {!blocked && warnings.length ? (
              <option value="aprobar_con_excepcion">Aprobar con excepción</option>
            ) : null}
            {!blocked ? <option value="aprobar">Habilitar para consulta</option> : null}
            <option value="rechazar">Rechazar</option>
          </Select>
        </div>

        {state.message ? (
          <p className={state.ok ? "text-[13px] text-ok" : "text-[13px] text-fail"}>
            {state.message}
          </p>
        ) : null}

        <Button type="submit" variant={blocked ? "danger" : "default"} disabled={pending}>
          {pending ? "Registrando…" : blocked ? "Registrar rechazo" : "Registrar decisión"}
        </Button>
      </form>
    </div>
  );
}
