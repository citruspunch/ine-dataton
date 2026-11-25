"use client";

import { useMemo, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  XAxis,
  YAxis,
} from "recharts";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart";
import { fmt } from "@/lib/format";
import type { CiiuSection, DinesePayload, ViewId } from "@/lib/types";

const config = {
  y2024: { label: "2024", color: "var(--chart-1)" },
  y2021: { label: "2021", color: "var(--chart-4)" },
  y2022: { label: "2022", color: "var(--chart-1)" },
} satisfies ChartConfig;

interface CiiuCardProps {
  view: ViewId;
  sections: CiiuSection[];
  current: DinesePayload;
  previous: DinesePayload | null;
}

export function CiiuCard({
  view,
  sections,
  current,
  previous,
}: CiiuCardProps) {
  const [expanded, setExpanded] = useState(false);
  const isSeries = view === "series";

  const rows = useMemo(
    () =>
      sections
        .map((section) => {
          const value = current.ciiu[section.letter] ?? 0;
          return {
            letter: section.letter,
            name: section.name,
            short: section.short,
            y2024: value,
            y2022: value,
            y2021: previous?.ciiu[section.letter] ?? 0,
          };
        })
        .sort((a, b) => {
          const aValue = isSeries ? a.y2022 : a.y2024;
          const bValue = isSeries ? b.y2022 : b.y2024;
          return bValue - aValue || a.name.localeCompare(b.name, "es");
        }),
    [sections, current, previous, isSeries],
  );

  const visible = expanded ? rows : rows.slice(0, 8);
  const height = visible.length * 36 + 20;

  const chartConfig: ChartConfig = isSeries
    ? { y2021: config.y2021, y2022: config.y2022 }
    : { y2024: config.y2024 };

  return (
    <Card className="shadow-sm">
      <CardContent className="flex h-full flex-col gap-4">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h2 className="text-base font-semibold tracking-tight">
              Actividad económica
            </h2>
            <p className="mt-0.5 text-[13px] text-muted-foreground">
              Establecimientos por sección CIIU · {current.year ?? 2024}
            </p>
          </div>
          <Badge
            variant="outline"
            className="h-6 rounded-full px-2.5 text-[11px] font-medium"
          >
            21 secciones
          </Badge>
        </div>

        {isSeries ? (
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5 text-[11.5px] text-muted-foreground">
              <span className="size-2 rounded-full bg-chart-4" />
              2021
            </span>
            <span className="flex items-center gap-1.5 text-[11.5px] text-muted-foreground">
              <span className="size-2 rounded-full bg-chart-1" />
              2022
            </span>
          </div>
        ) : null}

        <div className="overflow-x-auto">
          <div className="w-full">
            <ChartContainer
              config={chartConfig}
              className="aspect-auto w-full"
              style={{ height }}
            >
              <BarChart
                data={visible}
                layout="vertical"
                margin={{ top: 2, right: 46, left: 0, bottom: 2 }}
                barCategoryGap="24%"
              >
                <CartesianGrid horizontal={false} strokeDasharray="3 4" />
                <XAxis type="number" hide />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={170}
                  tickLine={false}
                  axisLine={false}
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value: string) => {
                    const row = rows.find((item) => item.name === value);
                    return row?.short ?? value;
                  }}
                />
                <ChartTooltip
                  content={
                    <ChartTooltipContent
                      indicator="dot"
                      formatter={(value, name) => (
                        <span className="flex w-full items-center justify-between gap-4">
                          <span className="text-muted-foreground">
                            {String(name).replace(/^y/, "")}
                          </span>
                          <span className="font-mono font-medium">
                            {fmt(Number(value))}
                          </span>
                        </span>
                      )}
                    />
                  }
                />
                {isSeries ? (
                  <>
                    <Bar
                      isAnimationActive={false}
                      dataKey="y2021"
                      fill="var(--color-y2021)"
                      radius={[0, 3, 3, 0]}
                      barSize={8}
                    />
                    <Bar
                      isAnimationActive={false}
                      dataKey="y2022"
                      fill="var(--color-y2022)"
                      radius={[0, 3, 3, 0]}
                      barSize={8}
                    >
                      <LabelList
                        dataKey="y2022"
                        position="right"
                        offset={6}
                        className="fill-muted-foreground"
                        fontSize={11.5}
                        formatter={(value) => fmt(Number(value))}
                      />
                    </Bar>
                  </>
                ) : (
                  <Bar
                    isAnimationActive={false}
                    dataKey="y2024"
                    fill="var(--color-y2024)"
                    radius={[0, 3, 3, 0]}
                    barSize={12}
                  >
                    <LabelList
                      dataKey="y2024"
                      position="right"
                      offset={6}
                      className="fill-muted-foreground"
                      fontSize={11.5}
                      formatter={(value) => fmt(Number(value))}
                    />
                  </Bar>
                )}
              </BarChart>
            </ChartContainer>
          </div>
        </div>

        <div className="mt-auto flex flex-wrap items-center justify-between gap-2 border-t border-dashed pt-3">
          <p className="text-[12px] leading-relaxed text-muted-foreground">
            Conteo de establecimientos; no es empleo ni ventas.
          </p>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 gap-1 px-2 text-[12px] text-primary"
            onClick={() => setExpanded((value) => !value)}
          >
            {expanded ? (
              <>
                Ver menos <ChevronUp className="size-3.5" />
              </>
            ) : (
              <>
                Ver las 21 secciones <ChevronDown className="size-3.5" />
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
