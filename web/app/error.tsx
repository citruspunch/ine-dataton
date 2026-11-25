"use client";

import { CircleAlert, RotateCcw } from "lucide-react";
import * as React from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  React.useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="paper-grain flex min-h-screen items-center justify-center px-4">
      <Card className="w-full max-w-lg border-destructive/30 shadow-xl">
        <CardHeader>
          <div className="flex items-center gap-2">
            <CircleAlert className="size-5 text-destructive" />
            <CardTitle className="font-display text-xl">
              Algo salió mal al dibujar el radar
            </CardTitle>
          </div>
          <CardDescription>
            La aplicación encontró un estado inesperado. Puede reintentar la vista o
            reconstruir los datos locales.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          <pre className="max-h-32 overflow-auto rounded-lg bg-muted p-3 text-xs text-muted-foreground">
            {error.message}
          </pre>
          <div className="flex flex-wrap gap-2">
            <Button onClick={reset}>
              <RotateCcw className="size-4" />
              Reintentar
            </Button>
            <Button variant="outline" asChild>
              <a href="/">Volver al inicio</a>
            </Button>
          </div>
          <p className="text-xs leading-relaxed text-muted-foreground">
            Si el problema persiste, ejecute <code className="rounded bg-muted px-1">uv run radar build</code>{" "}
            en la raíz y reinicie el servidor de Next.js.
          </p>
        </CardContent>
      </Card>
    </main>
  );
}
