import Link from "next/link";

import { loadExample, verifyAll } from "@/app/actions";
import { StateBadge } from "@/components/badges";
import { NewProfileDialog } from "@/components/new-profile-dialog";
import { UploadForm } from "@/components/upload-form";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { getJson } from "@/lib/api";
import type { CaseRow, ProfileSummary } from "@/lib/types";

export const dynamic = "force-dynamic";

interface PageProps {
  searchParams: Promise<{ msg?: string; kind?: string }>;
}

export default async function ReviewInboxPage({ searchParams }: PageProps) {
  const params = await searchParams;
  let cases: CaseRow[] = [];
  let profiles: ProfileSummary[] = [];
  let error = "";
  try {
    const [casesResponse, profilesResponse] = await Promise.all([
      getJson<{ cases: CaseRow[] }>("/review/cases"),
      getJson<{ profiles: ProfileSummary[] }>("/profiles"),
    ]);
    cases = casesResponse.cases;
    profiles = profilesResponse.profiles;
  } catch {
    error = "El motor de validación no está disponible. Arranque `pnpm run dev:engine`.";
  }

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">Bandeja de revisión técnica</h1>
        <p className="max-w-3xl text-[15px] text-muted">
          Cola local y privada. Aquí se valida, se justifica y se decide. Solo lo que un
          revisor habilita pasa al portal de consulta.
        </p>
      </header>

      {params.msg ? (
        <Alert variant={params.kind === "err" ? "fail" : params.kind === "warn" ? "warn" : "ok"}>
          {params.msg}
        </Alert>
      ) : null}
      {error ? <Alert variant="warn">{error}</Alert> : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex items-center justify-between gap-3">
            <CardTitle>Cargar un archivo</CardTitle>
            <NewProfileDialog />
          </CardHeader>
          <CardContent>
            <p className="mb-3 text-[13px] text-muted">
              El archivo se guarda en la cola privada, se le calcula el SHA-256 al
              recibirlo y se evalúa contra el perfil elegido.
            </p>
            <UploadForm profiles={profiles} />
            {profiles.some((profile) => !profile.valid) ? (
              <p className="mt-3 text-[12.5px] text-fail">
                Hay perfiles con errores de validación; el motor los rechazará al usarlos.
              </p>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Casos de ejemplo en un clic</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="mb-3 text-[13px] text-muted">
              Casos reales y fixtures sintéticos ya preparados. No hay que buscar archivos
              en el explorador.
            </p>
            <div className="space-y-2">
              {cases.map((row) => (
                <form
                  key={row.id}
                  action={loadExample}
                  className="flex items-center justify-between gap-3 rounded border border-line px-3 py-2"
                >
                  <input type="hidden" name="case_id" value={row.id} />
                  <div>
                    <p className="text-[13px] font-semibold">{row.label}</p>
                    <p className="font-mono text-[11.5px] text-muted">{row.id}</p>
                  </div>
                  <Button type="submit" variant="secondary" size="sm">
                    Cargar
                  </Button>
                </form>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <section className="space-y-3">
        <h2 className="text-[12px] font-semibold uppercase tracking-widest text-muted">
          Bandeja
        </h2>
        <Table>
          <THead>
            <TR>
              <TH>Caso</TH>
              <TH>Estado</TH>
              <TH>Perfil</TH>
              <TH>Críticas evaluadas</TH>
              <TH>Origen</TH>
              <TH />
            </TR>
          </THead>
          <TBody>
            {cases.map((row) => (
              <TR key={row.id}>
                <TD>
                  <Link href={`/review/${row.id}`} className="font-medium text-brand hover:underline">
                    {row.label}
                  </Link>
                  <div className="font-mono text-[11.5px] text-muted">{row.id}</div>
                </TD>
                <TD className="whitespace-nowrap">
                  <StateBadge state={row.state} text={row.state_text} />
                  {row.override ? <span className="ml-1 text-[11px] text-warn">simulación</span> : null}
                </TD>
                <TD className="font-mono text-[12px]">{row.profile}</TD>
                <TD className="whitespace-nowrap">{row.critical}</TD>
                <TD className="text-[12.5px] text-muted">{row.origin}</TD>
                <TD className="whitespace-nowrap">
                  <Link href={`/review/${row.id}`} className="text-[13px] text-brand underline">
                    Revisar
                  </Link>
                </TD>
              </TR>
            ))}
          </TBody>
        </Table>
      </section>

      <form action={verifyAll} className="flex items-center gap-3">
        <Button type="submit" variant="secondary">
          Verificar decisiones y digests
        </Button>
        <span className="text-[12.5px] text-muted">
          Retira del portal público cualquier agregado cuya decisión ya no sostenga el
          digest actual.
        </span>
      </form>
    </div>
  );
}
