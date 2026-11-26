"use client";

import { useState, useTransition } from "react";
import { CircleNotch, CopySimple, WarningCircle } from "@phosphor-icons/react/dist/ssr";

import { getProfileDefinition } from "@/app/actions";
import { NewProfileDialog } from "@/components/new-profile-dialog";
import { ProfileViewDialog } from "@/components/profile-view-dialog";
import { Button } from "@/components/ui/button";
import type { ProfileSummary } from "@/lib/types";

function nextCopyId(profileId: string, profiles: ProfileSummary[]) {
  const ids = new Set(profiles.map((profile) => profile.profile_id));
  const base = `${profileId}_copia`;
  if (!ids.has(base)) return base;
  let index = 2;
  while (ids.has(`${base}_${index}`)) index += 1;
  return `${base}_${index}`;
}

export function ProfileActions({
  profile,
  profiles,
}: {
  profile: ProfileSummary;
  profiles: ProfileSummary[];
}) {
  const [pending, startTransition] = useTransition();
  const [initialProfile, setInitialProfile] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState("");

  function duplicate() {
    setError("");
    startTransition(async () => {
      try {
        const definition = await getProfileDefinition(profile.profile_id);
        if (!definition.data) {
          throw new Error("El contrato no se pudo leer.");
        }
        setInitialProfile({
          ...definition.data,
          profile_id: nextCopyId(profile.profile_id, profiles),
          version: "1.0.0",
          title: `${String(definition.data.title || profile.title)} (copia)`,
        });
      } catch (cause) {
        setError(cause instanceof Error ? cause.message : "No se pudo duplicar el perfil.");
      }
    });
  }

  return (
    <div className="mt-2 flex flex-wrap items-center gap-1">
      <ProfileViewDialog profile={profile} />
      <Button type="button" variant="ghost" size="sm" onClick={duplicate} disabled={pending}>
        {pending ? (
          <CircleNotch className="h-3.5 w-3.5 animate-spin" aria-hidden />
        ) : (
          <CopySimple className="h-3.5 w-3.5" aria-hidden />
        )}
        Duplicar
      </Button>
      {error ? (
        <span className="flex items-center gap-1 text-[12px] text-fail">
          <WarningCircle className="h-3.5 w-3.5" aria-hidden />
          {error}
        </span>
      ) : null}
      {initialProfile ? (
        <NewProfileDialog
          key={String(initialProfile.profile_id)}
          title="Duplicar perfil de validación"
          initialProfile={initialProfile}
          openInitially
          trigger={null}
          onClosed={() => setInitialProfile(null)}
        />
      ) : null}
    </div>
  );
}
