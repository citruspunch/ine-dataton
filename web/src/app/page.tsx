import fs from "node:fs";
import path from "node:path";
import { Explorer } from "@/components/explorer";
import type { IndicatorsPayload } from "@/lib/types";

export const dynamic = "force-static";

function readPayload(): IndicatorsPayload | null {
  const candidates = [
    path.join(process.cwd(), "public", "data", "indicators.json"),
    path.join(process.cwd(), "..", "data", "processed", "indicators.json"),
  ];
  for (const candidate of candidates) {
    try {
      return JSON.parse(fs.readFileSync(candidate, "utf8")) as IndicatorsPayload;
    } catch {
      // Try the next location.
    }
  }
  return null;
}

export default function Page() {
  const data = readPayload();
  if (!data) {
    return (
      <main className="mx-auto flex min-h-screen max-w-3xl flex-col justify-center gap-4 px-6 py-16">
        <h1 className="text-2xl font-semibold">Faltan los datos procesados</h1>
        <p className="text-muted-foreground">
          Ejecute <code className="rounded bg-muted px-1.5 py-0.5">uv run build-pressure</code>{" "}
          desde la raíz del proyecto para descargar y procesar los datos, y luego{" "}
          <code className="rounded bg-muted px-1.5 py-0.5">pnpm dev</code> en{" "}
          <code className="rounded bg-muted px-1.5 py-0.5">web/</code>.
        </p>
      </main>
    );
  }
  return <Explorer data={data} />;
}
