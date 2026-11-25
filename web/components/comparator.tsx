"use client";

import { useActionState, useMemo } from "react";

import { comparePeriods } from "@/app/actions";
import { Button } from "@/components/ui/button";
import { Label, Select } from "@/components/ui/field";
import type { ActionState, ComparisonResult, Series } from "@/lib/types";
import { formatIndex, formatPct } from "@/lib/utils";

export function Comparator({
  caseId,
  series,
  defaults,
}: {
  caseId: string;
  series: Pick<Series, "series_id" | "label" | "base" | "points">[];
  defaults: { seriesA: string; periodA: string; seriesB: string; periodB: string };
}) {
  const [state, formAction, pending] = useActionState<ActionState, FormData>(comparePeriods, {
    ok: true,
  });

  const periods = useMemo(
    () => Array.from(new Set(series.flatMap((s) => s.points.map((p) => p.period)))).sort(),
    [series],
  );

  const result = state.result ?? null;

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <form action={formAction} className="rounded-md border border-line bg-card p-5">
        <input type="hidden" name="case_id" value={caseId} />
        <p className="mb-3 text-[13px] text-muted">
          Elija una serie y dos meses. Si son consecutivos y de la misma base, se muestra
          la variación <strong>publicada</strong> por el INE. Si el cruce no es válido, se
          bloquea y no se muestra ningún número calculado.
        </p>
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <Label htmlFor="series_a">Serie A (numerador)</Label>
            <Select id="series_a" name="series_a" defaultValue={defaults.seriesA}>
              {series.map((option) => (
                <option key={option.series_id} value={option.series_id}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label htmlFor="period_a">Periodo A</Label>
            <Select id="period_a" name="period_a" defaultValue={defaults.periodA}>
              {periods.map((period) => (
                <option key={period} value={period}>
                  {period}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label htmlFor="series_b">Serie B (denominador)</Label>
            <Select id="series_b" name="series_b" defaultValue={defaults.seriesB}>
              {series.map((option) => (
                <option key={option.series_id} value={option.series_id}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label htmlFor="period_b">Periodo B</Label>
            <Select id="period_b" name="period_b" defaultValue={defaults.periodB}>
              {periods.map((period) => (
                <option key={period} value={period}>
                  {period}
                </option>
              ))}
            </Select>
          </div>
        </div>
        <div className="mt-4">
          <Button type="submit" disabled={pending}>
            {pending ? "Comparando…" : "Comparar"}
          </Button>
        </div>
        {!state.ok && state.message ? (
          <p className="mt-3 text-[13px] text-fail">{state.message}</p>
        ) : null}
      </form>

      <div>
        {result ? <ResultCard result={result} /> : <EmptyCard />}
      </div>
    </div>
  );
}

function EmptyCard() {
  return (
    <div className="rounded-md border border-line bg-card p-5">
      <p className="text-[15px] font-semibold">Sin comparación todavía</p>
      <p className="mt-1 text-[13px] text-muted">
        Elija las series y los periodos y pulse Comparar. Por defecto está precargado el
        par válido de la serie base 2024=100.
      </p>
    </div>
  );
}

function ResultCard({ result }: { result: ComparisonResult }) {
  if (result.status === "ok") {
    return (
      <div className="rounded-md border border-[#b9dcc7] bg-ok-bg p-5 text-ok">
        <p className="text-[13px] opacity-80">Variación mensual publicada</p>
        <p className="my-1 text-4xl font-bold tracking-tight">
          {formatPct(result.published_pct)}
        </p>
        <p className="font-semibold">
          {result.period} respecto a {result.previous_period}
        </p>
        <p className="mt-2 text-[13px]">
          Serie {result.series_label} · base {result.base}
          <br />
          Índice {formatIndex(result.index_value)} ({result.index_cell}) sobre{" "}
          {formatIndex(result.previous_index_value)} · variación publicada en{" "}
          <span className="font-mono">{result.published_cell}</span>
        </p>
        <p className="mt-2 text-[12.5px] opacity-80">
          Regla {result.rule}. El prototipo muestra la cifra publicada; no la calcula.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-md border border-[#e7bdb9] bg-fail-bg p-5 text-fail">
      <p className="text-[13px] opacity-80">
        Comparación bloqueada · regla {result.rule ?? "—"}
      </p>
      <p className="mt-1 font-semibold">{result.message}</p>
      {result.detail ? (
        <dl className="mt-2 space-y-0.5 text-[13px]">
          {Object.entries(result.detail).map(([key, value]) => (
            <div key={key}>
              <dt className="inline font-semibold">{labelFor(key)}: </dt>
              <dd className="inline">{String(value)}</dd>
            </div>
          ))}
        </dl>
      ) : null}
      <p className="mt-2 text-[12.5px] opacity-80">
        No se muestra ningún valor: el prototipo no calcula una cifra que no esté
        publicada.
      </p>
    </div>
  );
}

function labelFor(key: string) {
  const labels: Record<string, string> = {
    base_a: "Base de la serie A",
    base_b: "Base de la serie B",
    guidance: "Qué hacer",
    months_between: "Meses entre periodos",
    missing_periods: "Periodos no publicados",
  };
  return labels[key] ?? key;
}
