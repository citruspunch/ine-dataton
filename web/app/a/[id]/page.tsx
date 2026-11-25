import Link from "next/link";
import { notFound } from "next/navigation";
import {
  ArrowLeft,
  ArrowUpRight,
  CalendarDots,
  DownloadSimple,
  FileText,
  Hash,
  ShieldCheck,
  Stack,
} from "@phosphor-icons/react/dist/ssr";

import { StateBadge } from "@/components/badges";
import { DataList, DataRow } from "@/components/data-list";
import { FindingsPanel } from "@/components/findings-panel";
import { PageHeader, SectionHeading } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getJson } from "@/lib/api";
import type { AggregateDetail, Receipt, Series } from "@/lib/types";
import { formatNumber, formatPct } from "@/lib/utils";

export const dynamic = "force-dynamic";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function PublicDetailPage({ params }: PageProps) {
  const { id } = await params;

  let payload: { aggregate: AggregateDetail; receipt: Receipt | null } | null = null;
  try {
    payload = await getJson(`/public/${id}`);
  } catch {
    payload = null;
  }
  if (!payload) notFound();

  const { aggregate } = payload;
  const entity = aggregate.entity;
  const series: Series[] = entity.series ?? [];

  const facts = [
    { label: "Periodo", value: entity.display.period ?? "—", icon: CalendarDots },
    { label: "Base", value: entity.display.base ?? "—", icon: Hash },
    { label: "Unidad", value: entity.display.unit ?? "—", icon: Stack },
    {
      label: "Licencia",
      value: entity.license.id || "sin licencia",
      icon: ShieldCheck,
    },
  ];

  return (
    <div className="space-y-7">
      <Link
        href="/"
        className="inline-flex items-center gap-1.5 text-[13px] font-semibold text-brand hover:underline print:hidden"
      >
        <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
        Volver a la consulta
      </Link>

      <PageHeader
        eyebrow="Consulta pública"
        title={entity.title || aggregate.label}
        description={
          <>
            Agregado publicado por el INE y habilitado para consulta el{" "}
            <span className="font-mono text-[12.5px]">
              {aggregate.published_at_utc?.slice(0, 10)}
            </span>
            . La validación es técnica y no sustituye la revisión oficial.
          </>
        }
        actions={
          <>
            <Link
              href={`/a/${aggregate.case_id}/ficha`}
              className={buttonVariants({ variant: "secondary", size: "sm" })}
            >
              <FileText className="h-3.5 w-3.5" aria-hidden />
              Ficha imprimible
            </Link>
            <Link
              href={`/api/receipt/${aggregate.case_id}`}
              className={buttonVariants({ variant: "secondary", size: "sm" })}
            >
              <DownloadSimple className="h-3.5 w-3.5" aria-hidden />
              recibo.json
            </Link>
          </>
        }
      />

      <div className="flex flex-wrap items-center gap-2">
        <StateBadge state={aggregate.state} text={aggregate.state_text} />
        {entity.topic === "ipc" ? <Badge variant="accent">IPC</Badge> : null}
        <Badge variant="none">no certifica</Badge>
        <span className="font-mono text-[11.5px] text-muted">{aggregate.case_id}</span>
      </div>

      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {facts.map((fact) => (
          <div
            key={fact.label}
            className="rounded-xl border border-line bg-white px-4 py-3 shadow-[0_1px_2px_rgba(16,32,52,.04)]"
          >
            <p className="flex items-center gap-1.5 text-[10.5px] font-bold uppercase tracking-[0.12em] text-muted">
              <fact.icon className="h-3.5 w-3.5 text-brand" aria-hidden />
              {fact.label}
            </p>
            <p className="mt-1.5 text-[14px] font-semibold leading-snug text-ink">
              {fact.value}
            </p>
          </div>
        ))}
      </section>

      <section className="space-y-4">
        <SectionHeading
          title="Series publicadas"
          description="Valores tomados de la fuente oficial, con la celda que los respalda."
        />
        {series.length ? (
          <div className="space-y-4">
            {series.map((item) => (
              <Card key={item.series_id}>
                <CardHeader className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <CardTitle>{item.label}</CardTitle>
                    <p className="mt-0.5 font-mono text-[11.5px] text-muted">
                      {item.series_id} · base {item.base ?? "no declarada"} ·{" "}
                      {item.unit ?? "sin unidad"}
                    </p>
                  </div>
                  <Badge variant={item.comparable ? "ok" : "warn"}>
                    {item.comparable ? "comparable" : "no comparable"}
                  </Badge>
                </CardHeader>
                {item.not_comparable_reason ? (
                  <div className="border-b border-line bg-warn-bg/50 px-5 py-2.5 text-[12.5px] leading-relaxed text-warn">
                    {item.not_comparable_reason}
                  </div>
                ) : null}
                <CardContent className="p-0">
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-[13px]">
                      <thead className="border-b border-line bg-[#f6f9fc] text-[10.5px] uppercase tracking-[0.1em] text-muted">
                        <tr>
                          <th className="px-5 py-2 font-bold">Periodo</th>
                          <th className="px-5 py-2 text-right font-bold">Índice</th>
                          {item.has_published_variation ? (
                            <th className="px-5 py-2 text-right font-bold">
                              Variación publicada
                            </th>
                          ) : null}
                          <th className="px-5 py-2 text-right font-bold">Celda</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-line">
                        {item.points.map((point) => (
                          <tr key={point.period} className="hover:bg-[#f8fbfe]">
                            <td className="px-5 py-2 font-mono text-[12px]">{point.period}</td>
                            <td className="px-5 py-2 text-right font-semibold tabular-nums">
                              {formatNumber(point.value)}
                            </td>
                            {item.has_published_variation ? (
                              <td className="px-5 py-2 text-right tabular-nums">
                                {formatPct(point.published_variation_pct)}
                              </td>
                            ) : null}
                            <td className="px-5 py-2 text-right font-mono text-[11.5px] text-muted">
                              {point.cell ?? "—"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <p className="rounded-lg border border-line bg-white px-4 py-6 text-[13px] text-muted">
            Este agregado no publica series en la consulta.
          </p>
        )}
      </section>

      <section className="grid gap-6 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <Card>
          <CardHeader>
            <CardTitle>Reglas evaluadas</CardTitle>
            <p className="mt-1 text-[13px] text-muted">
              Resultado técnico de cada regla aplicada al archivo.
            </p>
          </CardHeader>
          <CardContent className="p-0">
            <FindingsPanel findings={aggregate.findings} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Ficha técnica</CardTitle>
            <p className="mt-1 text-[13px] text-muted">
              Metadatos de procedencia y huella del archivo.
            </p>
          </CardHeader>
          <CardContent className="p-0">
            <DataList className="rounded-none border-0">
              <DataRow label="Fuente">
                {entity.title} · Instituto Nacional de Estadística
              </DataRow>
              <DataRow label="URL de origen">
                {entity.source_url ? (
                  <a
                    href={entity.source_url}
                    target="_blank"
                    rel="noreferrer"
                    className="break-all font-mono text-[11.5px] text-brand hover:underline"
                  >
                    {entity.source_url}
                    <ArrowUpRight className="ml-0.5 inline h-3 w-3" aria-hidden />
                  </a>
                ) : (
                  "—"
                )}
              </DataRow>
              <DataRow label="Descargado (UTC)">
                <span className="font-mono text-[12px]">
                  {entity.downloaded_at_utc || "—"}
                </span>
              </DataRow>
              <DataRow label="SHA-256">
                <span className="break-all font-mono text-[11.5px]">{entity.sha256}</span>
              </DataRow>
              <DataRow label="Licencia">
                {entity.license.id || "—"} · {entity.license.attribution || "—"}
              </DataRow>
              <DataRow label="Perfil">
                <span className="font-mono text-[12px]">{entity.profile}</span>
              </DataRow>
              <DataRow label="Digest">
                <span className="break-all font-mono text-[11.5px]">{aggregate.digest}</span>
              </DataRow>
            </DataList>
          </CardContent>
        </Card>
      </section>

      <p className="rounded-lg border border-line bg-brand-soft/60 px-4 py-3 text-[12px] leading-relaxed text-muted">
        {aggregate.notice}
      </p>
    </div>
  );
}
