import Link from "next/link";
import {
  ArrowRight,
  BadgeCheck,
  CircleAlert,
  ClipboardList,
  FilePlus2,
  Inbox,
  Layers3,
} from "lucide-react";

import { verifyAll } from "@/app/actions";
import { StateBadge } from "@/components/badges";
import { EmptyState } from "@/components/empty-state";
import { PageHeader, SectionHeading } from "@/components/page-header";
import { NewProfileDialog } from "@/components/new-profile-dialog";
import { UploadForm } from "@/components/upload-form";
import { VerifyButton } from "@/components/verify-button";
import { Alert } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TBody, TD, TH, THead, TR } from "@/components/ui/table";
import { getJson } from "@/lib/api";
import type { CaseRow, ProfileSummary } from "@/lib/types";

export const dynamic = "force-dynamic";

export const metadata = { title: "Revisión técnica" };

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
    error =
      "El motor de validación no está disponible. Verifique el servicio local antes de continuar.";
  }

  const pendingCount = cases.filter((row) => row.state === "en_revision").length;
  const invalidProfiles = profiles.filter((profile) => !profile.valid).length;

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Revisión técnica"
        title="Bandeja de validación"
        description="Cola privada donde cada archivo se contrasta con un contrato declarativo, se justifica y recibe una decisión humana. Solo lo habilitado aquí llega a la consulta pública."
        actions={
          <form action={verifyAll}>
            <VerifyButton />
          </form>
        }
      />

      {params.msg ? (
        <Alert variant={params.kind === "err" ? "fail" : params.kind === "warn" ? "warn" : "ok"}>
          <BadgeCheck className="h-4 w-4 shrink-0" aria-hidden />
          <span>{params.msg}</span>
        </Alert>
      ) : null}
      {error ? (
        <Alert variant="warn">
          <CircleAlert className="h-4 w-4 shrink-0" aria-hidden />
          <span>{error}</span>
        </Alert>
      ) : null}

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1.5fr)_minmax(0,1fr)]">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FilePlus2 className="h-4 w-4 text-brand" aria-hidden />
              Cargar un archivo
            </CardTitle>
            <CardDescription>
              Se calcula su SHA-256 al recibirlo y se evalúa contra el perfil declarado
              elegido. El archivo original no se modifica.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <UploadForm profiles={profiles} />
          </CardContent>
        </Card>

        <Card className="self-start">
          <CardHeader className="flex items-start justify-between gap-3">
            <div>
              <CardTitle className="flex items-center gap-2">
                <ClipboardList className="h-4 w-4 text-brand" aria-hidden />
                Perfiles declarativos
              </CardTitle>
              <CardDescription>
                Contratos que el motor aplica. {profiles.length} disponibles.
              </CardDescription>
            </div>
            <NewProfileDialog />
          </CardHeader>
          <CardContent className="px-0 py-0">
            {profiles.length ? (
              <ul className="divide-y divide-line">
                {profiles.map((profile) => (
                  <li key={profile.profile_id} className="px-5 py-3">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="text-[13.5px] font-semibold text-ink">
                          {profile.title}
                        </p>
                        <p className="mt-0.5 text-[11.5px] text-muted">
                          <span className="font-mono">{profile.profile_id}</span> · v
                          {profile.version} · {profile.kind_label}
                        </p>
                      </div>
                      {profile.valid ? (
                        <Badge variant="ok">válido</Badge>
                      ) : (
                        <Badge variant="fail">con errores</Badge>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="px-5 py-6 text-[13px] text-muted">
                No hay perfiles. Cree el primero con el editor de reglas.
              </p>
            )}
            {invalidProfiles ? (
              <p className="border-t border-line bg-fail-bg/60 px-5 py-2.5 text-[12px] text-fail">
                {invalidProfiles} perfil(es) no pasan la validación y serán rechazados por el
                motor.
              </p>
            ) : null}
            <div className="border-t border-line bg-[#fbfcfe] px-5 py-4">
              <p className="text-[10.5px] font-bold uppercase tracking-[0.12em] text-muted">
                Flujo de revisión
              </p>
              <ol className="mt-2 space-y-1.5 text-[12px] leading-relaxed text-muted">
                <li>1. Cargue el archivo y elija su contrato.</li>
                <li>2. Revise los hallazgos y justifique las advertencias.</li>
                <li>3. Registre la decisión: solo lo habilitado se publica.</li>
              </ol>
            </div>
          </CardContent>
        </Card>
      </div>

      <section className="space-y-4">
        <SectionHeading
          title="En la bandeja"
          description="Recursos registrados y archivos cargados en esta sesión."
          actions={
            <div className="flex items-center gap-2 text-[12.5px] text-muted">
              <Badge variant="outline">{cases.length} en total</Badge>
              {pendingCount ? <Badge variant="warn">{pendingCount} en revisión</Badge> : null}
            </div>
          }
        />

        {cases.length ? (
          <>
            <ul className="space-y-3 sm:hidden">
              {cases.map((row) => (
                <li key={row.id}>
                  <Link
                    href={`/review/${row.id}`}
                    className="block rounded-xl border border-line bg-white p-4 shadow-[0_1px_2px_rgba(16,32,52,.04)] transition-colors hover:border-[#b9c8da]"
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <StateBadge state={row.state} text={row.state_text} />
                      {row.override ? <Badge variant="warn">simulación</Badge> : null}
                    </div>
                    <p className="mt-2 text-[14px] font-semibold leading-snug text-brand">
                      {row.label}
                    </p>
                    <p className="mt-0.5 font-mono text-[11px] text-muted">{row.id}</p>
                    <dl className="mt-3 grid grid-cols-2 gap-x-3 gap-y-2 border-t border-line pt-3 text-[11.5px]">
                      <div className="col-span-2">
                        <dt className="text-[10px] uppercase tracking-wide text-muted">Perfil</dt>
                        <dd className="break-all font-mono text-[11px]">{row.profile}</dd>
                      </div>
                      <div>
                        <dt className="text-[10px] uppercase tracking-wide text-muted">Críticas</dt>
                        <dd>{row.critical}</dd>
                      </div>
                      <div>
                        <dt className="text-[10px] uppercase tracking-wide text-muted">Origen</dt>
                        <dd>{row.origin}</dd>
                      </div>
                    </dl>
                    <span className="mt-3 inline-flex items-center gap-1 text-[12.5px] font-semibold text-brand">
                      Revisar
                      <ArrowRight className="h-3.5 w-3.5" aria-hidden />
                    </span>
                  </Link>
                </li>
              ))}
            </ul>
            <div className="hidden sm:block">
              <Table>
                <THead>
              <TR>
                <TH>Caso</TH>
                <TH>Estado</TH>
                <TH>Perfil</TH>
                <TH>Críticas</TH>
                <TH>Origen</TH>
                <TH className="text-right">Acción</TH>
              </TR>
            </THead>
            <TBody>
              {cases.map((row) => (
                <TR key={row.id}>
                  <TD className="min-w-[240px]">
                    <Link
                      href={`/review/${row.id}`}
                      className="font-semibold text-brand hover:underline"
                    >
                      {row.label}
                    </Link>
                    <div className="mt-0.5 flex items-center gap-1.5 font-mono text-[11.5px] text-muted">
                      {row.id}
                      {row.override ? (
                        <span className="font-sans text-[11px] font-medium text-warn">
                          · simulación activa
                        </span>
                      ) : null}
                    </div>
                  </TD>
                  <TD className="whitespace-nowrap">
                    <StateBadge state={row.state} text={row.state_text} />
                  </TD>
                  <TD className="font-mono text-[12px] text-muted">{row.profile}</TD>
                  <TD className="whitespace-nowrap text-[13px]">{row.critical}</TD>
                  <TD className="whitespace-nowrap text-[12.5px] text-muted">{row.origin}</TD>
                  <TD className="whitespace-nowrap text-right">
                    <Link
                      href={`/review/${row.id}`}
                      className="inline-flex items-center gap-1 text-[13px] font-semibold text-brand hover:underline"
                    >
                      Revisar
                      <ArrowRight className="h-3.5 w-3.5" aria-hidden />
                    </Link>
                  </TD>
                </TR>
              ))}
            </TBody>
              </Table>
            </div>
          </>
        ) : (
          <EmptyState
            icon={Inbox}
            title="La bandeja está vacía"
            action={
              <span className="inline-flex items-center gap-2 text-[13px] text-muted">
                <Layers3 className="h-4 w-4" aria-hidden />
                Cargue un archivo para iniciar la primera revisión.
              </span>
            }
          >
            Cada archivo aparece aquí con su estado, el perfil aplicado y el avance de las
            reglas críticas.
          </EmptyState>
        )}
      </section>
    </div>
  );
}
