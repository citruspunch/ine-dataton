"use client";

import { useActionState, useState, useTransition } from "react";

import { createProfile, validateProfileYaml } from "@/app/actions";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input, Label, Textarea } from "@/components/ui/field";
import type { ActionState } from "@/lib/types";

const TEMPLATE = `profile_id: mi_contrato_v1
version: "1.0.0"
kind: xlsx
title: Mi contrato
description: >
  Describa qué archivo valida este contrato.
expected_sheet: Hoja1
header_row: 1

schema:
  - name: year
    column: "Año"
    type: integer
  - name: month
    column: "Mes"
    type: string
  - name: value
    column: "Índice"
    type: float

types: [integer, float, string]
grain: [year, month]

dates:
  year: year
  month: month
  month_format: name_es
  expected: ["2025-01", "2025-02"]

comparability:
  unit: índice
  series:
    - id: serie
      label: "Serie principal"
      index: value
      base: "2024=100"
      comparable: true
  checks: []
`;

export function NewProfileDialog() {
  const [state, formAction, pending] = useActionState<ActionState, FormData>(createProfile, {
    ok: true,
  });
  const [yaml, setYaml] = useState(TEMPLATE);
  const [errors, setErrors] = useState<{ field: string; message: string }[]>([]);
  const [checking, startChecking] = useTransition();

  function validate() {
    startChecking(async () => {
      const result = await validateProfileYaml(yaml);
      setErrors(result.errors);
    });
  }

  const shownErrors = errors.length ? errors : (state.errors ?? []);

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="secondary" type="button">
          Añadir regla (YAML)
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Nuevo perfil declarativo</DialogTitle>
          <DialogDescription>
            El motor valida sintaxis, campos obligatorios, tipos permitidos, grano,
            fechas y comparabilidad antes de guardar en <code>profiles/</code>.
          </DialogDescription>
        </DialogHeader>

        <form action={formAction} className="space-y-3">
          <div className="flex flex-wrap items-center gap-3 rounded border border-line bg-[#fafbfc] px-3 py-2">
            <label className="text-[12.5px] font-semibold text-muted" htmlFor="yaml-file">
              Cargar .yaml o .yml
            </label>
            <input
              id="yaml-file"
              type="file"
              accept=".yaml,.yml,text/yaml"
              className="text-[12.5px]"
              onChange={async (event) => {
                const file = event.target.files?.[0];
                if (file) setYaml(await file.text());
              }}
            />
            <span className="text-[12px] text-muted">
              Se carga en el editor; nada se guarda hasta validar y guardar.
            </span>
          </div>

          <div>
            <Label htmlFor="yaml">Contrato YAML</Label>
            <Textarea
              id="yaml"
              name="yaml"
              value={yaml}
              onChange={(event) => setYaml(event.target.value)}
              className="min-h-[320px] font-mono text-[12.5px]"
              spellCheck={false}
            />
          </div>

          <label className="flex items-center gap-2 text-[13px] text-muted">
            <input type="checkbox" name="overwrite" className="h-4 w-4" />
            Sobrescribir si el perfil ya existe
          </label>

          {shownErrors.length ? (
            <ul className="rounded border border-[#e7bdb9] bg-fail-bg px-3 py-2 text-[13px] text-fail">
              {shownErrors.map((error) => (
                <li key={`${error.field}-${error.message}`}>
                  <span className="font-mono">{error.field}</span>: {error.message}
                </li>
              ))}
            </ul>
          ) : null}

          {state.ok && state.message ? (
            <p className="rounded border border-[#b9dcc7] bg-ok-bg px-3 py-2 text-[13px] text-ok">
              {state.message} {state.profileId ? `(${state.profileId})` : ""}
            </p>
          ) : null}

          <div className="flex items-center gap-2">
            <Button type="submit" disabled={pending}>
              {pending ? "Guardando…" : "Guardar perfil"}
            </Button>
            <Button type="button" variant="secondary" onClick={validate} disabled={checking}>
              {checking ? "Validando…" : "Validar sin guardar"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
