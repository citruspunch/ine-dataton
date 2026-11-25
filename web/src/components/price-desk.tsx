"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Info, Loader2, Sparkles } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FindingsTable } from "@/components/findings-table";
import { Filters } from "@/components/filters";
import { Hero } from "@/components/hero";
import { Methodology } from "@/components/methodology";
import { PriceChecker } from "@/components/price-checker";
import { QualityPanel } from "@/components/quality-panel";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";
import { SourceIntegrity } from "@/components/source-integrity";
import { SourceSwitcher } from "@/components/source-switcher";
import { StatsCards } from "@/components/stats-cards";
import { defaultMetricForSource } from "@/lib/query";
import type {
  Catalog,
  DictionaryEntry,
  Manifest,
  QueryResult,
  SourceGroup,
  Summary,
} from "@/lib/types";

export function PriceDesk({
  initial,
  summary,
  manifest,
  catalog,
  dictionary,
}: {
  initial: QueryResult;
  summary: Summary;
  manifest: Manifest;
  catalog: Catalog;
  dictionary: DictionaryEntry[];
}) {
  const [source, setSource] = useState<SourceGroup>(initial.query.source);
  const [q, setQ] = useState(initial.query.q ?? "");
  const [from, setFrom] = useState(initial.query.from ?? "");
  const [to, setTo] = useState(initial.query.to ?? "");
  const [metric, setMetric] = useState(initial.selectedMetric ?? defaultMetricForSource(source));
  const [unit, setUnit] = useState(initial.selectedUnit ?? "");
  const [flaggedOnly, setFlaggedOnly] = useState(false);
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
    setFlaggedOnly(false);
    setPage(1);
  };

  const onChange = (patch: {
    source?: SourceGroup;
    q?: string;
    from?: string;
    to?: string;
    metric?: string;
    unit?: string;
    flagged?: boolean;
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
    if (patch.flagged !== undefined) {
      setFlaggedOnly(patch.flagged);
      setPage(1);
    }
  };

  const onClear = () => {
    setQ("");
    setFrom("");
    setTo("");
    setUnit("");
    unitTouched.current = false;
    setFlaggedOnly(false);
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
      if (flaggedOnly) params.set("flagged", "1");

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
            // A price band that mixes a ream with a pound is not comparable.
            // Default to the most frequent presentation of this search; the
            // user can still switch back to "Todas".
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
  }, [source, q, from, to, metric, unit, flaggedOnly, page]);

  const suggestions = useMemo(
    () => (catalog[source]?.items ?? []).slice(0, 500).map((item) => item.value),
    [catalog, source],
  );

  const group = summary.groups[source];

  return (
    <div className="min-h-screen">
      <SiteHeader summary={summary} />
      <Hero summary={summary} activeSource={source} />

      <main>
        <section id="consulta" className="mx-auto max-w-7xl px-4 pb-14 pt-8 sm:px-6 lg:px-8">
          <SourceSwitcher summary={summary} active={source} onChange={applySource} />

          <div className="mt-5">
            <Filters
              source={source}
              q={q}
              from={from}
              to={to}
              metric={metric}
              unit={unit}
              flaggedOnly={flaggedOnly}
              metrics={result.facets.metrics}
              units={result.facets.units}
              suggestions={suggestions}
              onChange={onChange}
              onClear={onClear}
            />
          </div>

          {error ? (
            <Alert variant="destructive" className="mt-4 bg-card">
              <Info className="size-4" aria-hidden />
              <AlertTitle>No se pudo consultar la API local</AlertTitle>
              <AlertDescription>
                {error}. Verifique que los datos estén generados con{" "}
                <code className="font-mono text-[11px]">uv run python -m procurement_prices build</code>.
              </AlertDescription>
            </Alert>
          ) : null}

          <div className="mt-4 flex items-start gap-2 rounded-xl border border-primary/15 bg-primary/[0.04] px-3.5 py-3 text-[11px] leading-relaxed text-foreground/80">
            <Sparkles className="mt-0.5 size-3.5 shrink-0 text-primary" aria-hidden />
            <p>
              <strong className="font-medium text-foreground">{group.label}.</strong>{" "}
              {group.coverageNote}
            </p>
          </div>

          {loading ? (
            <div className="mt-4 flex items-center gap-2 text-[10px] text-muted-foreground">
              <Loader2 className="size-3 animate-spin" aria-hidden />
              Actualizando la consulta…
            </div>
          ) : null}

          <div className="mt-6">
            <StatsCards result={result} />
          </div>

          <div className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1fr)_390px]">
            <div className="min-w-0 space-y-6">
              <FindingsTable result={result} loading={loading} onPageChange={setPage} />
              <QualityPanel
                result={result}
                flaggedOnly={flaggedOnly}
                onToggleFlagged={() => onChange({ flagged: !flaggedOnly })}
              />
            </div>
            <div className="space-y-6">
              <PriceChecker result={result} />
              <Card className="border-border/80 bg-card/80">
                <CardHeader className="pb-2">
                  <CardTitle className="font-heading text-lg">Cómo leer esta consulta</CardTitle>
                </CardHeader>
                <CardContent>
                  <ol className="space-y-2.5 text-[11px] leading-relaxed text-muted-foreground">
                    <li>
                      <span className="mr-1.5 inline-grid size-4 place-items-center rounded-full bg-primary/10 font-mono text-[9px] font-semibold text-primary">
                        1
                      </span>
                      Busque un producto o material. La coincidencia usa fragmentos y no distingue
                      tildes.
                    </li>
                    <li>
                      <span className="mr-1.5 inline-grid size-4 place-items-center rounded-full bg-primary/10 font-mono text-[9px] font-semibold text-primary">
                        2
                      </span>
                      Fije la presentación si hay varias. El rango sin presentación es solo una
                      señal amplia.
                    </li>
                    <li>
                      <span className="mr-1.5 inline-grid size-4 place-items-center rounded-full bg-primary/10 font-mono text-[9px] font-semibold text-primary">
                        3
                      </span>
                      Revise el corte y las alertas. Un dato congelado o parcial no se puede
                      presentar como precio vigente.
                    </li>
                  </ol>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>

        <SourceIntegrity manifest={manifest} activeSource={source} />
        <Methodology dictionary={dictionary} />
      </main>
      <SiteFooter />
    </div>
  );
}
