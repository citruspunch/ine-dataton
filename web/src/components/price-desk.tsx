"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Info, Loader2 } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { FindingsTable } from "@/components/findings-table";
import { Filters } from "@/components/filters";
import { PageIntro } from "@/components/page-intro";
import { PriceChecker } from "@/components/price-checker";
import { QualityPanel } from "@/components/quality-panel";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { StatsCards } from "@/components/stats-cards";
import { defaultMetricForSource } from "@/lib/query";
import type { Catalog, QueryResult, SourceGroup, Summary } from "@/lib/types";

const sourceContext: Record<SourceGroup, string> = {
  DPIR: "Instantáneas congeladas de precios observados en compras públicas. No es una serie mensual continua.",
  IPMC: "Índice mensual de 89 materiales, base diciembre 2018 = 100. Cobertura Región I Metropolitana.",
  ICC: "Índice de costos de vivienda social, base 2025 = 100. Solo 2026 y Región I; no es un precio.",
  BASKETS: "Costo por persona de la canasta alimentaria, 2024–2026. No es una cotización de mercado.",
};

export function PriceDesk({
  initial,
  summary,
  catalog,
}: {
  initial: QueryResult;
  summary: Summary;
  catalog: Catalog;
}) {
  const [source, setSource] = useState<SourceGroup>(initial.query.source);
  const [q, setQ] = useState(initial.query.q ?? "");
  const [from, setFrom] = useState(initial.query.from ?? "");
  const [to, setTo] = useState(initial.query.to ?? "");
  const [metric, setMetric] = useState(initial.selectedMetric ?? defaultMetricForSource(source));
  const [unit, setUnit] = useState(initial.selectedUnit ?? "");
  const [includeAlerts, setIncludeAlerts] = useState(false);
  const [page, setPage] = useState(initial.page);
  const [result, setResult] = useState<QueryResult>(initial);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const firstRender = useRef(true);
  const unitTouched = useRef(false);

  const applySource = (next: SourceGroup) => {
    if (next === source) return;
    setSource(next);
    setQ("");
    setFrom("");
    setTo("");
    setMetric(defaultMetricForSource(next));
    setUnit("");
    unitTouched.current = false;
    setIncludeAlerts(false);
    setPage(1);
  };

  const onChange = (patch: {
    source?: SourceGroup;
    q?: string;
    from?: string;
    to?: string;
    metric?: string;
    unit?: string;
    alerts?: boolean;
  }) => {
    if (patch.source && patch.source !== source) {
      applySource(patch.source);
      return;
    }
    if (patch.q !== undefined) {
      setQ(patch.q);
      setUnit("");
      unitTouched.current = false;
      setPage(1);
    }
    if (patch.from !== undefined) {
      setFrom(patch.from);
      setPage(1);
    }
    if (patch.to !== undefined) {
      setTo(patch.to);
      setPage(1);
    }
    if (patch.metric !== undefined) {
      setMetric(patch.metric);
      setUnit("");
      unitTouched.current = false;
      setPage(1);
    }
    if (patch.unit !== undefined) {
      setUnit(patch.unit);
      unitTouched.current = true;
      setPage(1);
    }
    if (patch.alerts !== undefined) {
      setIncludeAlerts(patch.alerts);
      setPage(1);
    }
  };

  const onClear = () => {
    setQ("");
    setFrom("");
    setTo("");
    setUnit("");
    unitTouched.current = false;
    setIncludeAlerts(false);
    setMetric(defaultMetricForSource(source));
    setPage(1);
  };

  useEffect(() => {
    if (firstRender.current) {
      firstRender.current = false;
      return;
    }
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams({
        source,
        page: String(page),
        pageSize: "25",
      });
      if (q.trim()) params.set("q", q.trim());
      if (from) params.set("from", from);
      if (to) params.set("to", to);
      if (metric) params.set("metric", metric);
      if (unit) params.set("unit", unit);
      if (includeAlerts) params.set("alerts", "1");

      fetch(`/api/records?${params.toString()}`, { signal: controller.signal })
        .then(async (response) => {
          if (!response.ok) {
            const body = (await response.json().catch(() => null)) as { error?: string } | null;
            throw new Error(body?.error ?? `Error ${response.status}`);
          }
          return (await response.json()) as QueryResult;
        })
        .then((data) => {
          setResult(data);
          if (data.selectedMetric && data.selectedMetric !== metric) {
            setMetric(data.selectedMetric);
          }
          const nextUnit = data.selectedUnit ?? "";
          const canAutoSelect =
            !unit &&
            !unitTouched.current &&
            q.trim().length > 0 &&
            data.facets.units.length > 1 &&
            data.facets.units.length <= 40;
          if (canAutoSelect) {
            setUnit(data.facets.units[0].label);
          } else if (nextUnit !== unit) {
            setUnit(nextUnit);
          }
          if (data.page !== page) setPage(data.page);
        })
        .catch((cause: unknown) => {
          if (cause instanceof DOMException && cause.name === "AbortError") return;
          setError(cause instanceof Error ? cause.message : "No se pudo consultar la API local.");
        })
        .finally(() => setLoading(false));
    }, q.trim() ? 260 : 80);

    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [source, q, from, to, metric, unit, includeAlerts, page]);

  const suggestions = useMemo(
    () => (catalog[source]?.items ?? []).slice(0, 500).map((item) => item.value),
    [catalog, source],
  );

  const alertCount = includeAlerts
    ? result.quality.duplicates +
      result.quality.invalidDate +
      result.quality.missingDate +
      result.quality.missingValue +
      result.quality.missingProduct
    : Math.max(0, result.quality.totalRecords - result.total);

  return (
    <div className="flex min-h-screen flex-col">
      <SiteHeader />
      <main className="flex-1">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <PageIntro summary={summary} />

          <section id="consulta" className="scroll-mt-20">
            <Filters
              source={source}
              q={q}
              from={from}
              to={to}
              metric={metric}
              unit={unit}
              includeAlerts={includeAlerts}
              alertCount={alertCount}
              metrics={result.facets.metrics}
              units={result.facets.units}
              suggestions={suggestions}
              onChange={onChange}
              onClear={onClear}
            />

            <div className="mt-4 flex items-start gap-2 text-[13px] leading-relaxed text-muted-foreground">
              <Info className="mt-0.5 size-3.5 shrink-0" aria-hidden />
              <p>
                <span className="font-medium text-foreground">
                  {summary.groups[source].label}.
                </span>{" "}
                {sourceContext[source]}
              </p>
            </div>

            {error ? (
              <Alert variant="destructive" className="mt-4 bg-card">
                <Info className="size-4" aria-hidden />
                <AlertTitle>No se pudo consultar la API local</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            ) : null}

            {loading ? (
              <div className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">
                <Loader2 className="size-3.5 animate-spin" aria-hidden />
                Actualizando…
              </div>
            ) : null}

            <div className="mt-8">
              <StatsCards result={result} />
            </div>

            <div className="mt-6 grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
              <FindingsTable
                result={result}
                loading={loading}
                includeAlerts={includeAlerts}
                onPageChange={setPage}
              />
              <div className="space-y-6">
                <PriceChecker result={result} />
                <QualityPanel result={result} includeAlerts={includeAlerts} />
              </div>
            </div>
          </section>

          <div className="mt-10 border-t border-border/60 py-6 text-sm text-muted-foreground">
            <p>
              ¿Necesita las URL, los hashes y las licencias?{" "}
              <a href="/fuentes" className="font-medium text-primary underline-offset-4 hover:underline">
                Ver fuentes y método
              </a>
              .
            </p>
          </div>
        </div>
      </main>
      <SiteFooter />
    </div>
  );
}
