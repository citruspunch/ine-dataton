"use client";

import * as React from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { areaData } from "@/lib/data";
import {
  formatQuetzales,
  shortGroupName,
} from "@/lib/format";
import type { Area, AreaMonth, Mode } from "@/lib/types";

type GroupBreakdownProps = {
  area: Area;
  month: AreaMonth;
  members: number;
  mode: Mode;
};

type Row = {
  name: string;
  value: number;
};

const VISIBLE = 6;

export function GroupBreakdown({
  area,
  month,
  members,
  mode,
}: GroupBreakdownProps) {
  const [expanded, setExpanded] = React.useState(false);
  const groups = areaData(area).groups;

  const rows: Row[] = React.useMemo(
    () =>
      month.groupValues
        .map((values, index) => ({
          name: groups[index] ?? `Grupo ${index + 1}`,
          value: mode === "total" ? values[0] * 30 * members : (values[2] ?? 0),
        }))
        .sort((a, b) => b.value - a.value),
    [month.groupValues, groups, mode, members],
  );

  const max = rows[0]?.value ?? 1;
  const visible = expanded ? rows : rows.slice(0, VISIBLE);

  return (
    <Card>
      <CardHeader className="pb-1">
        <div>
          <CardTitle className="text-[15px]">
            {mode === "total"
              ? "Gasto por grupo de alimentos"
              : "Costo por 1.000 kcal según grupo"}
          </CardTitle>
          <CardDescription className="mt-0.5 text-[13px]">
            {mode === "total"
              ? `Hogar de ${members} ${members === 1 ? "integrante" : "integrantes"} · ${month.label.toLowerCase()}`
              : `No depende del tamaño del hogar · ${month.label.toLowerCase()}`}
          </CardDescription>
        </div>
      </CardHeader>

      <CardContent className="pt-3">
        <div className="space-y-3.5">
          {visible.map((row) => (
            <div key={row.name}>
              <div className="flex items-baseline justify-between gap-3">
                <span className="truncate text-[14px] font-medium text-foreground">
                  {shortGroupName(row.name)}
                </span>
                <span className="shrink-0 font-mono text-[13.5px] tabular-nums text-foreground/80">
                  {formatQuetzales(row.value)}
                </span>
              </div>
              <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-muted">
                <div
                  className="h-full rounded-full bg-primary"
                  style={{ width: `${Math.max(2, (row.value / max) * 100)}%` }}
                />
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 flex items-center justify-between gap-3 border-t border-border/70 pt-3">
          <button
            type="button"
            onClick={() => setExpanded((current) => !current)}
            className="inline-flex items-center gap-1 text-[13px] font-medium text-primary transition-colors hover:text-primary/80"
          >
            {expanded ? (
              <>
                Ver menos
                <ChevronUp className="size-3.5" />
              </>
            ) : (
              <>
                Ver los {rows.length} grupos
                <ChevronDown className="size-3.5" />
              </>
            )}
          </button>
          {mode === "kcal" ? (
            <span className="text-[12px] text-muted-foreground">
              Excluye agua y sal
            </span>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}
