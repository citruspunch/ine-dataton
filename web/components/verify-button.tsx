"use client";

import { useFormStatus } from "react-dom";
import { ShieldCheck } from "@phosphor-icons/react/dist/ssr";

import { Button } from "@/components/ui/button";

export function VerifyButton() {
  const { pending } = useFormStatus();
  return (
    <Button type="submit" variant="secondary" disabled={pending}>
      <ShieldCheck className="h-4 w-4" aria-hidden />
      {pending ? "Verificando…" : "Verificar integridad"}
    </Button>
  );
}
