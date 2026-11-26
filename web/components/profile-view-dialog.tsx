"use client";

import { useState, useTransition } from "react";
import { CircleNotch, Eye } from "@phosphor-icons/react/dist/ssr";

import { getProfileDefinition } from "@/app/actions";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import type { ProfileDefinition, ProfileSummary } from "@/lib/types";

export function ProfileViewDialog({ profile }: { profile: ProfileSummary }) {
  const [open, setOpen] = useState(false);
  const [definition, setDefinition] = useState<ProfileDefinition | null>(null);
  const [error, setError] = useState("");
  const [pending, startTransition] = useTransition();

  function onOpenChange(next: boolean) {
    setOpen(next);
    if (!next || definition) return;
    setError("");
    startTransition(async () => {
      try {
        setDefinition(await getProfileDefinition(profile.profile_id));
      } catch {
        setError("No se pudo cargar el contrato.");
      }
    });
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        <Button type="button" variant="ghost" size="sm">
          <Eye className="h-3.5 w-3.5" aria-hidden />
          Ver
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>{profile.title}</DialogTitle>
          <DialogDescription>
            Vista de solo lectura. Para cambiar el contrato, duplíquelo y edite la copia.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[12.5px] text-muted">
            <span className="font-mono">{profile.profile_id}</span>
            <span>v{profile.version}</span>
            <span>{profile.kind_label}</span>
          </div>

          {pending ? (
            <p className="flex items-center gap-2 text-[13px] text-muted">
              <CircleNotch className="h-4 w-4 animate-spin" aria-hidden />
              Cargando el contrato…
            </p>
          ) : error ? (
            <p className="rounded-md border border-[#ffb699] bg-fail-bg px-3 py-2 text-[13px] text-fail">
              {error}
            </p>
          ) : definition ? (
            <pre className="max-h-[55vh] overflow-auto whitespace-pre-wrap break-words rounded-md bg-[#1a1a1a] p-3 font-mono text-[12.5px] leading-relaxed text-[#f0f0f0]">
              {definition.yaml}
            </pre>
          ) : null}
        </div>
      </DialogContent>
    </Dialog>
  );
}
