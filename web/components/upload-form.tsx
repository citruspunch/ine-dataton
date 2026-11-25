"use client";

import { useActionState } from "react";

import { uploadCase } from "@/app/actions";
import { Button } from "@/components/ui/button";
import { Label, Input, Select } from "@/components/ui/field";
import type { ActionState, ProfileSummary } from "@/lib/types";

const LICENSES = [
  { value: "cc-by", label: "cc-by (CC BY verificada)" },
  { value: "interno-fixture", label: "interno-fixture (sintético)" },
  { value: "sin-licencia", label: "sin licencia (cierra el recurso)" },
];

export function UploadForm({ profiles }: { profiles: ProfileSummary[] }) {
  const [state, formAction, pending] = useActionState<ActionState, FormData>(uploadCase, {
    ok: true,
  });

  return (
    <form action={formAction} className="space-y-3">
      <div>
        <Label htmlFor="file">Archivo (.csv, .xlsx, .xls)</Label>
        <Input id="file" name="file" type="file" accept=".csv,.xlsx,.xls" required />
      </div>
      <div>
        <Label htmlFor="profile">Perfil declarativo</Label>
        <Select id="profile" name="profile" required defaultValue={profiles[0]?.profile_id}>
          {profiles.map((profile) => (
            <option key={profile.profile_id} value={profile.profile_id}>
              {profile.title} · v{profile.version} ({profile.kind_label})
            </option>
          ))}
        </Select>
      </div>
      <div>
        <Label htmlFor="license">Licencia verificada</Label>
        <Select id="license" name="license" defaultValue="cc-by">
          {LICENSES.map((license) => (
            <option key={license.value} value={license.value}>
              {license.label}
            </option>
          ))}
        </Select>
      </div>
      {!state.ok && state.message ? (
        <p className="text-[13px] text-fail">{state.message}</p>
      ) : null}
      <Button type="submit" disabled={pending}>
        {pending ? "Validando…" : "Validar archivo"}
      </Button>
    </form>
  );
}
