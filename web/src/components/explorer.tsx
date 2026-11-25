"use client";

import * as React from "react";
import {
  Activity,
  Database,
  Info,
  Search,
  X,
} from "lucide-react";
import {
  Card,
  CardContent,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { IndicatorChart } from "@/components/indicator-chart";
import { MunicipalityTable } from "@/components/municipality-table";
import { MunicipalitySheet } from "@/components/municipality-sheet";
import { SourcesPanel } from "@/components/sources-panel";
import { formatInteger, formatPercent, formatUtc, normalizeSearch } from "@/lib/format";
import type { IndicatorsPayload, Municipality } from "@/lib/types";

function StatCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: React.ReactNode;
  hint: string;
}) {
  return (
    <Card className="gap-0 py-0">
      <CardContent className="p-5">
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
          {label}
        </p>
        <p className="mt-2 text-3xl font-semibold tracking-tight tabular-nums">{value}</p>
        <p className="mt-1 text-xs leading-snug text-muted-foreground">{hint}</p>
      </CardContent>
    </Card>
  );
}

export function Explorer({ data }: { data: IndicatorsPayload }) {
  const pressureKeys = data.pressure_indicator_keys;
  const firstDepartment =
    data.departments.find((item) => item.codigo === "01")?.codigo ??
    data.departments[0]?.codigo ??
    "all";

  const [department, setDepartment] = React.useState(firstDepartment);
  const [indicatorKey, setIndicatorKey] = React.useState(
    pressureKeys[0] ?? "crecimiento_poblacional_pct",
  );
  const [search, setSearch] = React.useState("");
  const [tab, setTab] = React.useState("explorador");
  const [selected, setSelected] = React.useState<Municipality | null>(null);
  const [departmentOnly, setDepartmentOnly] = React.useState(firstDepartment !== "all");

  React.useEffect(() => {
    setDepartmentOnly(department !== "all");
  }, [department]);

  const definition = data.indicators.find((item) => item.key === indicatorKey);
  const departmentRows = React.useMemo(
    () =>
      data.municipalities.filter(
        (municipality) =>
          department === "all" || municipality.departamento_codigo === department,
      ),
    [data.municipalities, department],
  );
  const departmentName =
    department === "all"
      ? "Todos los departamentos"
      : data.departments.find((item) => item.codigo === department)?.nombre ?? "Departamento";

  const stats = React.useMemo(() => {
    const population = departmentRows.reduce(
      (total, municipality) => total + (municipality.poblacion_2025 ?? 0),
      0,
    );
    const population2035 = departmentRows.reduce(
      (total, municipality) => total + (municipality.poblacion_2035 ?? 0),
      0,
    );
    const growth =
      population > 0 ? ((population2035 - population) / population) * 100 : null;
    const highPressure = departmentRows.filter(
      (municipality) => municipality.presion[indicatorKey]?.clase === "alta",
    ).length;
    return { population, population2035, growth, highPressure };
  }, [departmentRows, indicatorKey]);

  const tableDepartmentFilter = departmentOnly ? department : "all";
  const searchMatches = React.useMemo(() => {
    const needle = normalizeSearch(search);
    if (!needle) return departmentRows.length;
    return data.municipalities.filter((municipality) => {
      if (
        tableDepartmentFilter !== "all" &&
        municipality.departamento_codigo !== tableDepartmentFilter
      ) {
        return false;
      }
      const haystack = normalizeSearch(
        `${municipality.municipio_codigo} ${municipality.municipio_nombre} ${municipality.departamento_nombre}`,
      );
      return haystack.includes(needle);
    }).length;
  }, [data.municipalities, departmentRows.length, search, tableDepartmentFilter]);

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-30 border-b bg-background/85 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-5">
          <div className="flex min-w-0 items-center gap-3">
            <div className="grid size-9 shrink-0 place-items-center rounded-xl bg-primary text-primary-foreground shadow-sm">
              <Activity className="size-4" />
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold leading-tight">Presión local</p>
              <p className="truncate text-[11px] text-muted-foreground">
                Guatemala · Datatón INE 2026
              </p>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2 sm:gap-3">
            <span className="hidden text-xs text-muted-foreground sm:inline">
              Corte {data.snapshot_id}
            </span>
            <Button variant="outline" size="sm" onClick={() => setTab("fuentes")}>
              <Database className="size-3.5" />
              <span className="hidden sm:inline">Datos y fuentes</span>
              <span className="sm:hidden">Fuentes</span>
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-5 py-9 sm:py-12">
        <section className="max-w-2xl">
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-primary">
            Monitoreo municipal
          </p>
          <h1 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">
            Dónde la demanda crece más rápido que los servicios
          </h1>
          <p className="mt-3 text-base leading-relaxed text-muted-foreground">
            Compare municipios de un departamento con tres señales: crecimiento poblacional,
            nacimientos por escuela y presión de la asignación constitucional.
          </p>
        </section>

        <div className="mt-6 flex flex-wrap items-center gap-x-3 gap-y-2 text-xs text-muted-foreground">
          <span className="inline-flex items-center gap-1.5 rounded-full border bg-muted/30 px-3 py-1.5">
            <Info className="size-3.5" />
            Herramienta independiente, no oficial
          </span>
          <span>SEGEPLAN CC BY-NC 2.0 · MINEDUC CC0</span>
          <button
            type="button"
            onClick={() => setTab("fuentes")}
            className="font-medium text-foreground underline underline-offset-4 hover:text-primary"
          >
            Ver licencias
          </button>
        </div>

        <Tabs value={tab} onValueChange={setTab} className="mt-8 gap-0">
          <TabsList
            variant="line"
            className="h-auto w-full justify-start gap-6 border-b bg-transparent p-0"
          >
            <TabsTrigger
              value="explorador"
              className="flex-none rounded-none border-0 bg-transparent px-0 pb-3 shadow-none focus-visible:bg-muted/50 focus-visible:ring-0 focus-visible:outline-none data-[state=active]:border-0 data-[state=active]:bg-transparent data-[state=active]:shadow-none"
            >
              Explorador
            </TabsTrigger>
            <TabsTrigger
              value="fuentes"
              className="flex-none rounded-none border-0 bg-transparent px-0 pb-3 shadow-none focus-visible:bg-muted/50 focus-visible:ring-0 focus-visible:outline-none data-[state=active]:border-0 data-[state=active]:bg-transparent data-[state=active]:shadow-none"
            >
              Datos y fuentes
            </TabsTrigger>
          </TabsList>

          <TabsContent value="explorador" className="mt-7 space-y-6">
            <Card>
              <CardContent className="grid gap-4 p-4 md:grid-cols-[1fr_1.2fr_1.15fr] md:items-start">
                <div className="min-w-0 space-y-1.5">
                  <label htmlFor="department" className="text-xs font-medium text-muted-foreground">
                    Departamento
                  </label>
                  <Select value={department} onValueChange={setDepartment}>
                    <SelectTrigger id="department" className="w-full min-w-0 bg-background">
                      <SelectValue placeholder="Todos los departamentos" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Todos los departamentos</SelectItem>
                      {data.departments.map((item) => (
                        <SelectItem key={item.codigo} value={item.codigo}>
                          {item.codigo} · {item.nombre} ({item.municipios})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="min-w-0 space-y-1.5">
                  <label htmlFor="indicator" className="text-xs font-medium text-muted-foreground">
                    Indicador de presión
                  </label>
                  <Select value={indicatorKey} onValueChange={setIndicatorKey}>
                    <SelectTrigger id="indicator" className="w-full min-w-0 bg-background">
                      <SelectValue placeholder="Indicador" />
                    </SelectTrigger>
                    <SelectContent>
                      {data.indicators
                        .filter((item) => pressureKeys.includes(item.key))
                        .map((item) => (
                          <SelectItem key={item.key} value={item.key}>
                            {item.short_label}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="min-w-0 space-y-1.5">
                  <label
                    htmlFor="municipality-search"
                    className="text-xs font-medium text-muted-foreground"
                  >
                    Buscar municipio
                  </label>
                  <div className="relative">
                    <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
                    <Input
                      id="municipality-search"
                      value={search}
                      onChange={(event) => setSearch(event.target.value)}
                      placeholder="Nombre, código o departamento"
                      className="bg-background pl-9 pr-9"
                    />
                    {search ? (
                      <button
                        type="button"
                        onClick={() => setSearch("")}
                        aria-label="Limpiar búsqueda"
                        className="absolute right-2 top-1/2 grid size-6 -translate-y-1/2 place-items-center rounded-full text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
                      >
                        <X className="size-3.5" />
                      </button>
                    ) : null}
                  </div>
                  {search ? (
                    <p className="text-[11px] text-muted-foreground">
                      {searchMatches} {searchMatches === 1 ? "coincidencia" : "coincidencias"}
                    </p>
                  ) : null}
                </div>
              </CardContent>
            </Card>

            <div className="grid gap-3 sm:grid-cols-3">
              <StatCard
                label="Población 2025"
                value={formatInteger(stats.population)}
                hint={`${departmentRows.length} municipios`}
              />
              <StatCard
                label="Crecimiento 2025–35"
                value={formatPercent(stats.growth)}
                hint={`${formatInteger(stats.population2035 - stats.population)} personas más`}
              />
              <StatCard
                label="Presión alta"
                value={`${stats.highPressure}`}
                hint={`de ${departmentRows.length} · ${definition?.short_label ?? "indicador"}`}
              />
            </div>

            <Card>
              <CardContent className="p-5 sm:p-6">
                <IndicatorChart
                  data={data}
                  department={department}
                  indicatorKey={indicatorKey}
                  onShowSources={() => setTab("fuentes")}
                />
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-5 sm:p-6">
                <MunicipalityTable
                  data={data}
                  search={search}
                  indicatorKey={indicatorKey}
                  departmentFilter={departmentOnly ? department : "all"}
                  departmentName={departmentName}
                  onToggleDepartment={() => setDepartmentOnly((current) => !current)}
                  onClearSearch={() => setSearch("")}
                  onOpenMunicipality={setSelected}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="fuentes" className="mt-7">
            <SourcesPanel data={data} />
          </TabsContent>
        </Tabs>
      </main>

      <footer className="border-t bg-muted/20">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-5 py-6 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <p>INE · MINEDUC · SEGEPLAN. SEGEPLAN CC BY-NC 2.0, uso no comercial.</p>
          <p>
            Corte {data.snapshot_id} · Generado {formatUtc(data.generated_at_utc)} · Herramienta
            independiente.
          </p>
        </div>
      </footer>

      <MunicipalitySheet
        data={data}
        municipality={selected}
        onOpenChange={(open) => {
          if (!open) setSelected(null);
        }}
      />
    </div>
  );
}
