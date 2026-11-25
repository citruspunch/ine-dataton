"use client";

import { CircleAlert } from "lucide-react";

import { Button } from "@/components/ui/button";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="mx-auto flex max-w-xl flex-col items-center gap-4 py-20 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-fail-bg text-fail">
        <CircleAlert className="h-6 w-6" aria-hidden />
      </span>
      <h1 className="text-2xl font-semibold tracking-tight">Algo falló al cargar la página</h1>
      <p className="text-[14px] leading-relaxed text-muted">
        {error.message || "El motor de validación no respondió. Intente de nuevo."}
      </p>
      <Button onClick={reset}>Reintentar</Button>
    </div>
  );
}
