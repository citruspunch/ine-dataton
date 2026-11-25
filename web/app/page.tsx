"use client";

import {
  Baby,
  CarFront,
  ChevronDown,
  CircleAlert,
  HeartPulse,
  Map as MapIcon,
  Radar,
  Search,
  ShieldCheck,
} from "lucide-react";
import * as React from "react";

import { DetailPanel } from "@/components/detail-panel";
import { MethodologySheet } from "@/components/methodology-sheet";
import { TerritoryMap } from "@/components/territory-map";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { loadDataset, type Dataset } from "@/lib/data";
import { formatNumber, formatRate } from "@/lib/format";
import { makeQuantileScale } from "@/lib/scale";
import type { Cell, Criterion, CriterionId, LevelId, Mode, TopicId } from "@/lib/types";
import { cn } from "@/lib/utils";

const PALETTES: Record<TopicId, string[]> = {
  road_safety: ["#fff4e6", "#fdc38d", "#f28e5b", "#d95f3b", "#8c2d24"],
  births: ["#e8f5f2", "#b2e0d5", "#6fc4b6", "#2f9188", "#0f4f4a"],
  deaths: ["#f4ebf7", "#d9b8e8", "#b47fd1", "#7e3fa8", "#4a1d70"],
};

const TOPIC_LABELS: Record<TopicId, string> = {
  road_safety: "Tránsito",
  births: "Nacimientos",
  deaths: "Defunciones",
};

const CRITERION_LABELS: Record<CriterionId, string> = {
  residence: "Residencia",
  occurrence: "Ocurrencia",
};

const LEVEL_LABELS: Record<LevelId, string> = {
  department: "Departamento",
  municipality: "Municipio",
};

function normalizeText(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function nationalOf(criterion: Criterion): Cell {
  return criterion.available
    ? criterion.national
    : { suppressed: true, threshold: 5 };
}

function valueOf(cell: Cell | undefined, mode: Mode): number | null {
  if (!cell || cell.suppressed) return null;
  return mode === "rate" ? cell.rate : cell.count;
}

function uiMetrics(dataset: Dataset, topicId: TopicId) {
  return Object.values(dataset.indicators.topics[topicId].metrics).filter(
    (metric) => !(topicId === "road_safety" && metric.id === "vehicles"),
  );
}

export default function HomePage() {
  const [data, setData] = React.useState<Dataset | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [methodologyOpen, setMethodologyOpen] = React.useState(false);

  const [topicId, setTopicId] = React.useState<TopicId>("road_safety");
  const [metricId, setMetricId] = React.useState("incidents");
  const [criterionId, setCriterionId] = React.useState<CriterionId>("occurrence");
  const [level, setLevel] = React.useState<LevelId>("department");
  const [mode, setMode] = React.useState<Mode>("rate");
  const [selected, setSelected] = React.useState("01");
  const [showPoints, setShowPoints] = React.useState(true);
  const [search, setSearch] = React.useState("");
  const [sortKey, setSortKey] = React.useState("value-desc");
  const [visibleRows, setVisibleRows] = React.useState(22);

  React.useEffect(() => {
    let cancelled = false;
    loadDataset()
      .then((dataset) => {
        if (!cancelled) setData(dataset);
      })
      .catch((reason: unknown) => {
        if (!cancelled) {
          setError(reason instanceof Error ? reason.message : String(reason));
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  React.useEffect(() => {
    setVisibleRows(level === "department" ? 22 : 15);
  }, [level, search, sortKey, topicId, metricId, mode]);

  if (!data) {
    return (
      <div className="min-h-screen bg-background">
        <SiteHeader onOpenMethodology={() => setMethodologyOpen(true)} />
        <main className="mx-auto w-full max-w-[1400px] px-4 pb-12 pt-8 sm:px-6 lg:px-8">
          {error ? (
            <Card className="mx-auto mt-16 max-w-xl border-destructive/30 shadow-lg">
              <CardContent className="space-y-4 p-6">
                <div className="flex items-center gap-2">
                  <CircleAlert className="size-5 text-destructive" />
                  <h2 className="font-display text-xl font-semibold">
                    No se pudieron cargar los datos
                  </h2>
                </div>
                <p className="text-sm text-muted-foreground">{error}</p>
                <pre className="overflow-x-auto rounded-lg bg-muted p-3 text-sm">
                  uv run radar build{"\n"}cd web && pnpm dev
                </pre>
              </CardContent>
            </Card>
          ) : (
            <LoadingState />
          )}
        </main>
      </div>
    );
  }

  const topic = data.indicators.topics[topicId];
  const metrics = uiMetrics(data, topicId);
  const metric = metrics.find((item) => item.id === metricId) ?? metrics[0];
  const criterion = metric.criteria[criterionId];
  const available = criterion.available;
  const levelCells = available ? criterion.levels[level].cells : {};
  const levelPayload = available ? criterion.levels[level] : null;

  const departments = data.territories.departments;
  const municipalities = data.territories.municipalities;
  const nameByCode = new Map<string, string>([
    ...departments.map((item) => [item.code, item.name] as const),
    ...municipalities.map((item) => [item.code, item.name] as const),
  ]);

  const selectedDepartment =
    level === "department"
      ? departments.find((item) => item.code === selected) ?? departments[0]
      : null;
  const municipality =
    level === "municipality"
      ? municipalities.find((item) => item.code === selected) ?? municipalities[0]
      : null;

  const territory = municipality
    ? {
        code: municipality.code,
        name: municipality.name,
        parent: municipality.deptName,
        population: municipality.population,
        census2018: municipality.census2018,
      }
    : {
        code: selectedDepartment?.code ?? selected,
        name: selectedDepartment?.name ?? "Guatemala",
        parent: "Guatemala",
        population: selectedDepartment?.population ?? 0,
        census2018: selectedDepartment?.census2018 ?? 0,
      };

  const cell = levelCells[territory.code];
  const scaleValues = available
    ? Object.values(levelCells)
        .filter(
          (item): item is Extract<Cell, { suppressed: false }> =>
            !item.suppressed,
        )
        .map((item) => (mode === "rate" ? item.rate : item.count))
    : [];
  const scale =
    scaleValues.length > 0
      ? makeQuantileScale(scaleValues, PALETTES[topicId], 5)
      : null;

  const ranked = Object.entries(levelCells)
    .filter(
      (entry): entry is [string, Extract<Cell, { suppressed: false }>] =>
        !entry[1].suppressed,
    )
    .map(([code, item]) => ({ code, rate: item.rate }))
    .sort((a, b) => b.rate - a.rate);
  const rankMap = new Map(ranked.map((row, index) => [row.code, index + 1] as const));

  const geo = level === "department" ? data.departamentos : data.municipios;
  const sourceRows =
    level === "department"
      ? departments.map((item) => ({
          code: item.code,
          name: item.name,
          parent: "—",
          population: item.population,
          cell: levelCells[item.code],
        }))
      : municipalities.map((item) => ({
          code: item.code,
          name: item.name,
          parent: item.deptName,
          population: item.population,
          cell: levelCells[item.code],
        }));

  const filteredRows = sourceRows.filter((row) => {
    if (!search.trim()) return true;
    return normalizeText(`${row.name} ${row.parent}`).includes(
      normalizeText(search.trim()),
    );
  });
  const sortedRows = [...filteredRows].sort((a, b) => {
    if (sortKey === "name") return a.name.localeCompare(b.name, "es");
    if (sortKey === "population") return b.population - a.population;
    const av = valueOf(a.cell, mode);
    const bv = valueOf(b.cell, mode);
    if (av === null && bv === null) return a.name.localeCompare(b.name, "es");
    if (av === null) return 1;
    if (bv === null) return -1;
    return sortKey === "value-asc" ? av - bv : bv - av;
  });
  const rowsToShow = sortedRows.slice(0, visibleRows);
  const publishedCount = sourceRows.filter(
    (row) => row.cell && !row.cell.suppressed,
  ).length;
  const suppressedCount = levelPayload?.suppressed_territories ?? 0;

  const nationalStats = [
    {
      label: "Nacimientos",
      cell: nationalOf(
        data.indicators.topics.births.metrics.births.criteria.residence,
      ),
    },
    {
      label: "Defunciones",
      cell: nationalOf(
        data.indicators.topics.deaths.metrics.deaths.criteria.occurrence,
      ),
    },
    {
      label: "Hechos de tránsito",
      cell: nationalOf(
        data.indicators.topics.road_safety.metrics.incidents.criteria.occurrence,
      ),
    },
  ];

  const handleTopicChange = (next: TopicId) => {
    setTopicId(next);
    const nextMetrics = uiMetrics(data, next);
    if (!nextMetrics.some((item) => item.id === metricId)) {
      setMetricId(nextMetrics[0]?.id ?? "incidents");
    }
  };

  const handleLevelChange = (next: LevelId) => {
    setLevel(next);
    if (next === "department") {
      setSelected(selected.slice(0, 2));
    } else if (selected.length === 2) {
      const first = municipalities.find((item) => item.dept === selected);
      setSelected(first?.code ?? municipalities[0]?.code ?? "0101");
    } else if (!municipalities.some((item) => item.code === selected)) {
      setSelected(municipalities[0]?.code ?? "0101");
    }
  };

  const handleSelect = (code: string) => {
    setSelected(code);
    if (typeof window !== "undefined" && window.innerWidth < 1024) {
      window.setTimeout(() => {
        document
          .getElementById("detalle")
          ?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 90);
    }
  };

  const legendValue = (value: number) =>
    mode === "rate" ? formatRate(value) : formatNumber(value);

  return (
    <div className="min-h-screen bg-background">
      <SiteHeader onOpenMethodology={() => setMethodologyOpen(true)} />

      <main className="mx-auto w-full max-w-[1400px] px-4 pb-12 sm:px-6 lg:px-8">
        <section className="flex flex-wrap items-end justify-between gap-8 border-b border-border/60 py-8">
          <div className="max-w-2xl">
            <p className="text-sm font-medium text-primary">Guatemala · 2025</p>
            <h1 className="mt-1 font-display text-4xl font-semibold tracking-tight sm:text-5xl">
              Riesgo territorial en salud y tránsito
            </h1>
            <p className="mt-3 text-sm leading-relaxed text-muted-foreground sm:text-base">
              Compare nacimientos, defunciones y siniestralidad vial con tasas por
              10.000 habitantes. Residencia y ocurrencia se muestran por separado,
              con secreto estadístico aplicado en cada celda.
            </p>
          </div>
          <dl className="flex flex-wrap gap-x-8 gap-y-4">
            {nationalStats.map((stat) => (
              <div key={stat.label}>
                <dt className="text-xs text-muted-foreground">{stat.label}</dt>
                <dd className="tabular mt-1 text-2xl font-semibold leading-none">
                  {stat.cell.suppressed ? "—" : formatNumber(stat.cell.count)}
                </dd>
                <dd className="mt-1 text-xs text-muted-foreground">
                  {stat.cell.suppressed
                    ? "sin dato"
                    : `${formatRate(stat.cell.rate)} por 10 mil`}
                </dd>
              </div>
            ))}
          </dl>
        </section>

        <section className="py-5">
          <Card className="border-border/70 bg-card/80 shadow-none">
            <CardContent className="flex flex-wrap items-end gap-x-6 gap-y-4 p-4">
              <ControlGroup label="Tema">
                <ToggleGroup
                  type="single"
                  value={topicId}
                  onValueChange={(value) => value && handleTopicChange(value as TopicId)}
                  className="rounded-lg border bg-muted/35 p-1"
                >
                  {(["road_safety", "births", "deaths"] as TopicId[]).map((id) => {
                    const Icon =
                      id === "road_safety"
                        ? CarFront
                        : id === "births"
                          ? Baby
                          : HeartPulse;
                    return (
                      <ToggleGroupItem
                        key={id}
                        value={id}
                        className="h-8 gap-1.5 rounded-md px-3 text-xs data-[state=on]:bg-primary data-[state=on]:text-primary-foreground data-[state=on]:shadow-sm"
                      >
                        <Icon className="size-3.5" />
                        {TOPIC_LABELS[id]}
                      </ToggleGroupItem>
                    );
                  })}
                </ToggleGroup>
              </ControlGroup>

              {metrics.length > 1 ? (
                <ControlGroup label="Indicador">
                  <Select value={metric.id} onValueChange={setMetricId}>
                    <SelectTrigger className="h-9 w-56 bg-card text-sm">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {metrics.map((item) => (
                        <SelectItem key={item.id} value={item.id}>
                          {item.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </ControlGroup>
              ) : null}

              <ControlGroup label="Criterio">
                <ToggleGroup
                  type="single"
                  value={criterionId}
                  onValueChange={(value) =>
                    value && setCriterionId(value as CriterionId)
                  }
                  className="rounded-lg border bg-muted/35 p-1"
                >
                  <ToggleGroupItem
                    value="residence"
                    title={
                      topic.onlyOccurrence
                        ? "La PNC solo publica datos por ocurrencia"
                        : undefined
                    }
                    className="h-8 rounded-md px-3 text-xs data-[state=on]:bg-primary data-[state=on]:text-primary-foreground data-[state=on]:shadow-sm"
                  >
                    Residencia
                  </ToggleGroupItem>
                  <ToggleGroupItem
                    value="occurrence"
                    className="h-8 rounded-md px-3 text-xs data-[state=on]:bg-primary data-[state=on]:text-primary-foreground data-[state=on]:shadow-sm"
                  >
                    Ocurrencia
                  </ToggleGroupItem>
                </ToggleGroup>
              </ControlGroup>

              <ControlGroup label="Nivel">
                <ToggleGroup
                  type="single"
                  value={level}
                  onValueChange={(value) =>
                    value && handleLevelChange(value as LevelId)
                  }
                  className="rounded-lg border bg-muted/35 p-1"
                >
                  <ToggleGroupItem
                    value="department"
                    className="h-8 rounded-md px-3 text-xs data-[state=on]:bg-primary data-[state=on]:text-primary-foreground data-[state=on]:shadow-sm"
                  >
                    Departamento
                  </ToggleGroupItem>
                  <ToggleGroupItem
                    value="municipality"
                    className="h-8 rounded-md px-3 text-xs data-[state=on]:bg-primary data-[state=on]:text-primary-foreground data-[state=on]:shadow-sm"
                  >
                    Municipio
                  </ToggleGroupItem>
                </ToggleGroup>
              </ControlGroup>

              <ControlGroup label="Unidad">
                <ToggleGroup
                  type="single"
                  value={mode}
                  onValueChange={(value) => value && setMode(value as Mode)}
                  className="rounded-lg border bg-muted/35 p-1"
                >
                  <ToggleGroupItem
                    value="rate"
                    className="h-8 rounded-md px-3 text-xs data-[state=on]:bg-primary data-[state=on]:text-primary-foreground data-[state=on]:shadow-sm"
                  >
                    Tasa
                  </ToggleGroupItem>
                  <ToggleGroupItem
                    value="count"
                    className="h-8 rounded-md px-3 text-xs data-[state=on]:bg-primary data-[state=on]:text-primary-foreground data-[state=on]:shadow-sm"
                  >
                    Conteo
                  </ToggleGroupItem>
                </ToggleGroup>
              </ControlGroup>

              {!available ? (
                <Badge
                  variant="outline"
                  className="mb-0.5 gap-1 rounded-full border-amber-300 bg-amber-50 text-xs text-amber-900"
                >
                  Sin datos por residencia
                </Badge>
              ) : null}
            </CardContent>
          </Card>
        </section>

        <section className="grid items-start gap-5 lg:grid-cols-[minmax(0,1.55fr)_minmax(340px,0.8fr)]">
          <Card className="overflow-hidden border-border/70 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-3 border-b px-5 py-4">
              <div>
                <div className="flex items-center gap-2">
                  <MapIcon className="size-4 text-primary" />
                  <h2 className="text-base font-semibold">Mapa</h2>
                </div>
                <p className="mt-1 text-sm text-muted-foreground">
                  {metric.label} ·{" "}
                  {mode === "rate" ? "tasa por 10.000 hab." : "conteo"} ·{" "}
                  {CRITERION_LABELS[criterionId]} · {data.meta.dataYear}
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-4">
                <label className="flex cursor-pointer items-center gap-2 text-xs text-muted-foreground">
                  <Switch checked={showPoints} onCheckedChange={setShowPoints} />
                  Puntos
                </label>
                <Badge variant="outline" className="rounded-full text-xs">
                  {level === "department" ? "22 departamentos" : "340 municipios"}
                </Badge>
              </div>
            </div>
            <div className="bg-[#eef3f0]">
              <TerritoryMap
                level={level}
                geo={geo}
                selected={territory.code}
                onSelect={handleSelect}
                cellFor={(code) => levelCells[code]}
                nameFor={(code) => nameByCode.get(code) ?? code}
                scale={scale}
                mode={mode}
                points={data.points.points}
                showPoints={showPoints && available}
                available={available}
                unavailableTitle="La PNC no publica residencia"
                unavailableMessage={criterion.available ? undefined : criterion.reason}
                onUseOccurrence={!available ? () => setCriterionId("occurrence") : undefined}
                className="h-[480px] sm:h-[600px] xl:h-[640px]"
              />
            </div>
            <div className="flex flex-wrap items-center justify-between gap-3 border-t px-5 py-3 text-xs text-muted-foreground">
              {scale ? (
                <div className="flex flex-wrap items-center gap-2">
                  <span className="tabular">{legendValue(scale.min)}</span>
                  <div className="flex h-2 w-36 overflow-hidden rounded-full">
                    {scale.colors.map((color) => (
                      <span
                        key={color}
                        className="flex-1"
                        style={{ backgroundColor: color }}
                      />
                    ))}
                  </div>
                  <span className="tabular">{legendValue(scale.max)}</span>
                  <span className="ml-2 inline-flex items-center gap-1.5">
                    <span className="size-2 rounded-[2px] bg-[repeating-linear-gradient(45deg,#f1eee8,#f1eee8_2px,#d8d2c7_2px,#d8d2c7_4px)]" />
                    Suprimido
                  </span>
                </div>
              ) : (
                <span>Sin datos publicables para esta combinación.</span>
              )}
              <div className="flex items-center gap-3">
                <span className="hidden sm:inline">
                  Haz clic en un territorio para ver su ficha
                </span>
                <span className="inline-flex items-center gap-1.5">
                  <ShieldCheck className="size-3.5 text-primary" />
                  Celdas &lt; 5 suprimidas
                </span>
              </div>
            </div>
          </Card>

          <div id="detalle" className="scroll-mt-24">
            <DetailPanel
              level={level}
              topicId={topicId}
              metric={metric}
              criterionId={criterionId}
              criterion={criterion}
              mode={mode}
              territory={territory}
              cell={cell}
              publicCells={levelCells}
              deathCauses={data.deathCauses}
              onShowOccurrence={() => setCriterionId("occurrence")}
            />
          </div>
        </section>

        <section className="mt-8" id="territorios">
          <Card className="overflow-hidden border-border/70 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b px-5 py-4">
              <div>
                <h2 className="text-base font-semibold">Explorar territorios</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  {LEVEL_LABELS[level]} · {CRITERION_LABELS[criterionId]} ·{" "}
                  {metric.label}
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <div className="relative">
                  <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                    placeholder="Buscar territorio"
                    className="h-9 w-56 bg-card pl-8 text-sm"
                    aria-label="Buscar territorio"
                  />
                </div>
                <Select value={sortKey} onValueChange={setSortKey}>
                  <SelectTrigger className="h-9 w-40 bg-card text-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="value-desc">
                      Mayor {mode === "rate" ? "tasa" : "conteo"}
                    </SelectItem>
                    <SelectItem value="value-asc">
                      Menor {mode === "rate" ? "tasa" : "conteo"}
                    </SelectItem>
                    <SelectItem value="name">Nombre A–Z</SelectItem>
                    <SelectItem value="population">Población</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Table>
                <TableHeader className="bg-card">
                  <TableRow>
                    <TableHead
                      className="hidden w-14 pl-5 text-xs font-medium sm:table-cell"
                      title="Posición según la tasa por 10.000 habitantes"
                    >
                      Rank
                    </TableHead>
                    <TableHead className="text-xs font-medium">Territorio</TableHead>
                    <TableHead className="hidden text-right text-xs font-medium md:table-cell">
                      Población
                    </TableHead>
                    <TableHead className="hidden text-right text-xs font-medium sm:table-cell">
                      Casos
                    </TableHead>
                    <TableHead className="text-right text-xs font-medium">
                      Tasa / 10 mil
                    </TableHead>
                    <TableHead className="pr-5 text-right text-xs font-medium">
                      Estado
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rowsToShow.map((row) => {
                    const publicCell =
                      row.cell && !row.cell.suppressed ? row.cell : null;
                    const isSelected = row.code === territory.code;
                    return (
                      <TableRow
                        key={row.code}
                        className={cn(
                          "cursor-pointer text-sm transition-colors hover:bg-muted/40",
                          isSelected && "bg-primary/[0.055]",
                        )}
                        onClick={() => handleSelect(row.code)}
                      >
                        <TableCell className="tabular hidden py-2.5 pl-5 text-muted-foreground sm:table-cell">
                          {rankMap.get(row.code) ?? "—"}
                        </TableCell>
                        <TableCell className="py-2.5">
                          <p className="font-medium leading-tight">{row.name}</p>
                          {level === "municipality" ? (
                            <p className="mt-0.5 text-xs text-muted-foreground">
                              {row.parent}
                            </p>
                          ) : null}
                        </TableCell>
                        <TableCell className="tabular hidden py-2.5 text-right text-muted-foreground md:table-cell">
                          {formatNumber(row.population)}
                        </TableCell>
                        <TableCell className="tabular hidden py-2.5 text-right sm:table-cell">
                          {publicCell ? formatNumber(publicCell.count) : "—"}
                        </TableCell>
                        <TableCell className="tabular py-2.5 text-right">
                          {publicCell ? formatRate(publicCell.rate) : "—"}
                        </TableCell>
                        <TableCell className="py-2.5 pr-5 text-right">
                          <span className="inline-flex items-center gap-1.5 text-xs">
                            <span
                              className={cn(
                                "size-1.5 rounded-full",
                                publicCell
                                  ? "bg-emerald-500"
                                  : !available
                                    ? "bg-stone-400"
                                    : "bg-amber-500",
                              )}
                            />
                            {publicCell
                              ? "Publicado"
                              : !available
                                ? "No disponible"
                                : "Suprimido"}
                          </span>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
              {rowsToShow.length === 0 ? (
                <p className="px-5 py-12 text-center text-sm text-muted-foreground">
                  No hay territorios que coincidan con “{search}”.
                </p>
              ) : null}
            </div>
            <div className="flex flex-wrap items-center justify-between gap-3 border-t bg-muted/15 px-5 py-3 text-xs text-muted-foreground">
              <span>
                {rowsToShow.length}{" "}
                {rowsToShow.length === 1 ? "resultado" : "resultados"} ·{" "}
                {available ? (
                  <>
                    {publishedCount} publicados
                    {search.trim() ? " en total" : ""}
                    {suppressedCount > 0
                      ? ` · ${suppressedCount} suprimidos`
                      : ""}
                  </>
                ) : (
                  "sin datos por residencia"
                )}
              </span>
              {visibleRows < sortedRows.length ? (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-8 text-xs"
                  onClick={() => setVisibleRows((value) => value + 30)}
                >
                  Mostrar más
                  <ChevronDown className="size-3.5" />
                </Button>
              ) : null}
            </div>
          </Card>
        </section>

        <footer className="mt-10 flex flex-wrap items-center justify-between gap-3 border-t border-border/60 pt-5 text-xs text-muted-foreground">
          <p>
            Fuente: INE Guatemala · Límites: geoBoundaries / OCHA FISS · Datos 2025
          </p>
          <button
            type="button"
            onClick={() => setMethodologyOpen(true)}
            className="font-medium text-primary hover:underline"
          >
            Metodología, fuentes y licencias
          </button>
        </footer>
      </main>

      <MethodologySheet
        open={methodologyOpen}
        onOpenChange={setMethodologyOpen}
        meta={data.meta}
      />
    </div>
  );
}

function SiteHeader({ onOpenMethodology }: { onOpenMethodology: () => void }) {
  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-background/90 backdrop-blur-xl">
      <div className="mx-auto flex w-full max-w-[1400px] items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <div className="relative flex size-9 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-sm">
            <Radar className="size-5" />
            <span className="absolute -right-0.5 -top-0.5 size-2.5 rounded-full border-2 border-background bg-accent" />
          </div>
          <div className="min-w-0">
            <p className="truncate font-display text-base font-semibold leading-tight tracking-tight">
              Radar territorial
            </p>
            <p className="truncate text-xs text-muted-foreground">
              Salud y tránsito · Guatemala 2025
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="hidden items-center gap-1.5 text-xs text-muted-foreground sm:flex">
            <span className="size-1.5 rounded-full bg-emerald-500" />
            Fuentes INE verificadas
          </span>
          <Button
            variant="outline"
            size="sm"
            className="h-8 text-xs"
            onClick={onOpenMethodology}
          >
            Metodología
          </Button>
        </div>
      </div>
    </header>
  );
}

function ControlGroup({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      {children}
    </div>
  );
}

function LoadingState() {
  return (
    <div className="space-y-6 pt-10">
      <Skeleton className="h-28 w-full rounded-2xl" />
      <Skeleton className="h-16 w-full rounded-xl" />
      <div className="grid gap-5 lg:grid-cols-[1.55fr_0.8fr]">
        <Skeleton className="h-[560px] rounded-xl" />
        <Skeleton className="h-[560px] rounded-xl" />
      </div>
      <Skeleton className="h-64 w-full rounded-xl" />
    </div>
  );
}
