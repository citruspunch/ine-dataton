"use client";

import { useMemo, useState } from "react";
import { ChevronDown, CircleAlert } from "lucide-react";

import { SeverityBadge } from "@/components/badges";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Finding, Severity } from "@/lib/types";

const FILTERS: { value: "todas" | Severity; label: string }[] = [
  { value: "todas", label: "Todas" },
  { value: "falla", label: "Fallas" },
  { value: "advertencia", label: "Advertencias" },
  { value: "no_evaluado", label: "No evaluadas" },
  { value: "ok", label: "Conformes" },
];

export function FindingsPanel({ findings }: { findings: Finding[] }) {
  const [filter, setFilter] = useState<"todas" | Severity>("todas");

  const counts = useMemo(() => {
    const base: Record<string, number> = { todas: findings.length };
    for (const finding of findings) base[finding.status] = (base[finding.status] ?? 0) + 1;
    return base;
  }, [findings]);

  const visible = filter === "todas" ? findings : findings.filter((f) => f.status === filter);

  return (
    <div>
      <div className="flex flex-wrap gap-1.5 border-b border-line px-4 py-3">
        {FILTERS.filter((item) => item.value === "todas" || counts[item.value]).map((item) => (
          <button
            key={item.value}
            type="button"
            onClick={() => setFilter(item.value)}
            aria-pressed={filter === item.value}
            className={cn(
              "rounded-full border px-2.5 py-1 text-[11.5px] font-semibold transition-colors",
              filter === item.value
                ? "border-brand bg-brand text-white"
                : "border-line bg-white text-muted hover:border-[#b9c8da] hover:text-brand",
            )}
          >
            {item.label}
            <span
              className={cn(
                "ml-1.5 rounded-full px-1.5 text-[10.5px]",
                filter === item.value ? "bg-white/20" : "bg-none-bg",
              )}
            >
              {counts[item.value] ?? 0}
            </span>
          </button>
        ))}
      </div>

      {visible.length ? (
        <ul className="divide-y divide-line">
          {visible.map((finding) => (
            <li key={finding.rule_id}>
              <details className="group">
                <summary className="flex cursor-pointer list-none flex-wrap items-start gap-3 px-4 py-3 transition-colors hover:bg-[#f8fbfe]">
                  <div className="flex min-w-0 flex-1 items-start gap-3">
                    <span className="mt-0.5 shrink-0">
                      <SeverityBadge status={finding.status} />
                    </span>
                    <div className="min-w-0">
                      <p className="text-[13px] font-semibold text-ink">
                        {finding.title}
                        {finding.critical ? (
                          <span className="ml-2 align-middle text-[10.5px] font-bold uppercase tracking-wide text-brand">
                            crítica
                          </span>
                        ) : null}
                      </p>
                      <p className="mt-0.5 text-[12.5px] leading-relaxed text-muted">
                        {finding.message}
                      </p>
                      <p className="mt-1 font-mono text-[11px] text-muted/80">{finding.rule_id}</p>
                    </div>
                  </div>
                  <ChevronDown
                    className="mt-1 h-4 w-4 shrink-0 text-muted transition-transform group-open:rotate-180"
                    aria-hidden
                  />
                </summary>
                <div className="border-t border-line bg-[#fbfcfe] px-4 py-3">
                  <p className="mb-1.5 text-[11px] font-bold uppercase tracking-[0.1em] text-muted">
                    Evidencia
                  </p>
                  {Object.keys(finding.evidence ?? {}).length ? (
                    <pre className="max-h-72 overflow-auto whitespace-pre-wrap break-words rounded-md border border-line bg-white p-3 font-mono text-[11px] leading-relaxed text-ink">
                      {JSON.stringify(finding.evidence, null, 2)}
                    </pre>
                  ) : (
                    <p className="text-[12px] text-muted">Sin evidencia registrada.</p>
                  )}
                  {finding.justified ? (
                    <Badge variant="ok" className="mt-2">
                      excepción justificada
                    </Badge>
                  ) : null}
                </div>
              </details>
            </li>
          ))}
        </ul>
      ) : (
        <p className="flex items-center gap-2 px-4 py-6 text-[13px] text-muted">
          <CircleAlert className="h-4 w-4" aria-hidden />
          No hay hallazgos en esta categoría.
        </p>
      )}
    </div>
  );
}
