"use client";

import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  AlertTriangle,
  Database,
  ExternalLink,
  RefreshCw,
} from "lucide-react";
import { BrandMark } from "@/components/brand-mark";
import { CiiuCard } from "@/components/ciiu-card";
import { KpiCards } from "@/components/kpi-cards";
import { LegalCard } from "@/components/legal-card";
import { NoticeBanner } from "@/components/notice-banner";
import { PlacesCard } from "@/components/places-card";
import { PopulationCard } from "@/components/population-card";
import { SizeCard } from "@/components/size-card";
import { SourcesDialog } from "@/components/sources-dialog";
import { TerritoryPicker } from "@/components/territory-picker";
import { TimeJump } from "@/components/time-jump";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useBootstrap, useProfile } from "@/lib/use-data";
import type { ViewId } from "@/lib/types";

function AppHeader({
  view,
  onViewChange,
}: {
  view: ViewId;
  onViewChange: (view: ViewId) => void;
}) {
  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-background/95 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-[1180px] items-center justify-between gap-3 px-5 lg:px-8">
        <div className="flex min-w-0 items-center gap-2.5">
          <BrandMark className="size-9" />
          <div className="min-w-0">
            <div className="text-[15px] font-semibold tracking-tight">
              Perfil Municipal
            </div>
            <div className="hidden text-[12px] text-muted-foreground sm:block">
              Censo 2018 · DINESE
            </div>
          </div>
        </div>
        <TimeJump view={view} onChange={onViewChange} />
      </div>
    </header>
  );
}

function Intro() {
  return (
    <section className="pb-6 pt-8 lg:pt-10">
      <p className="text-[13px] text-muted-foreground">
        Guatemala · 340 municipios
      </p>
      <h1 className="mt-1.5 text-[2rem] font-semibold leading-tight tracking-tight sm:text-[2.4rem]">
        Perfil de demanda municipal
      </h1>
      <p className="mt-2.5 max-w-2xl text-[15px] leading-relaxed text-muted-foreground">
        Población, empresas registradas y territorio. El corte 2024 se lee por
        separado de la serie 2021–2022 para no confundir cobertura con
        crecimiento.
      </p>
    </section>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-[136px] w-full rounded-xl" />
      <Skeleton className="h-[90px] w-full rounded-xl" />
      <div className="grid gap-4 sm:grid-cols-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <Skeleton key={index} className="h-[132px] rounded-xl" />
        ))}
      </div>
      <div className="grid gap-4 lg:grid-cols-12">
        <Skeleton className="h-[340px] rounded-xl lg:col-span-7" />
        <Skeleton className="h-[340px] rounded-xl lg:col-span-5" />
        <Skeleton className="h-[400px] rounded-xl lg:col-span-8" />
        <Skeleton className="h-[400px] rounded-xl lg:col-span-4" />
        <Skeleton className="h-[560px] rounded-xl lg:col-span-12" />
      </div>
    </div>
  );
}

function LoadError({ message }: { message: string }) {
  return (
    <Card className="mx-auto mt-8 max-w-2xl border-destructive/30">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <AlertTriangle className="size-4 text-destructive" />
          No se pudieron cargar los datos
        </CardTitle>
        <CardDescription>{message}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <p className="text-muted-foreground">
          Genera los artefactos locales desde la raíz del proyecto. La
          aplicación no requiere servicios en la nube ni llaves de acceso.
        </p>
        <pre className="overflow-x-auto rounded-lg bg-secondary/60 p-3 font-mono text-xs">
          uv run municipal-profile all{"\n"}
          cd web && pnpm install && pnpm dev
        </pre>
        <div className="flex flex-wrap gap-2">
          <Button onClick={() => window.location.reload()} className="gap-1.5">
            <RefreshCw className="size-3.5" />
            Reintentar
          </Button>
          <Button
            variant="outline"
            className="gap-1.5"
            onClick={() =>
              window.open("/data/manifest.json", "_blank", "noopener,noreferrer")
            }
          >
            <Database className="size-3.5" />
            Ver manifiesto
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function HomePageContent() {
  const { meta, territories, error } = useBootstrap();
  const searchParams = useSearchParams();
  const requestedView = searchParams.get("vista");
  const requestedMunicipality = searchParams.get("municipio");
  const initialCode =
    requestedMunicipality && /^\d{4}$/.test(requestedMunicipality)
      ? requestedMunicipality
      : "0101";

  const [view, setView] = useState<ViewId>(
    requestedView === "series" ? "series" : "2024",
  );
  const [departmentCode, setDepartmentCode] = useState(initialCode.slice(0, 2));
  const [municipalityCode, setMunicipalityCode] = useState(initialCode);
  const [sourcesOpen, setSourcesOpen] = useState(false);

  const requested = useMemo(
    () =>
      territories?.municipalities.find(
        (item) => item.code === municipalityCode,
      ) ?? null,
    [territories, municipalityCode],
  );

  const fallbackMunicipality =
    territories?.municipalities.find((item) => item.code === "0101") ??
    territories?.municipalities[0] ??
    null;

  const municipality = requested ?? fallbackMunicipality;
  const effectiveMunicipalityCode = municipality?.code ?? initialCode;
  const effectiveDepartmentCode =
    municipality?.department_code ?? departmentCode;

  const { profile, loading, error: profileError } = useProfile(
    effectiveMunicipalityCode,
    Boolean(meta && territories),
  );

  useEffect(() => {
    const url = new URL(window.location.href);
    url.searchParams.set("vista", view);
    url.searchParams.set("municipio", effectiveMunicipalityCode);
    window.history.replaceState(null, "", url.toString());
  }, [view, effectiveMunicipalityCode]);

  function handleDepartmentChange(code: string) {
    setDepartmentCode(code);
    const options =
      territories?.municipalities.filter(
        (item) => item.department_code === code,
      ) ?? [];
    if (options.length) {
      const largest = [...options].sort(
        (a, b) => b.population - a.population,
      )[0];
      setMunicipalityCode(largest.code);
    }
  }

  function handleMunicipalityChange(code: string) {
    setMunicipalityCode(code);
    const match = territories?.municipalities.find(
      (item) => item.code === code,
    );
    if (match) setDepartmentCode(match.department_code);
  }

  const viewConfig = meta?.views.find((item) => item.id === view);
  const notice = viewConfig?.notice ?? meta?.notices?.[view];

  const current =
    profile && view === "2024"
      ? profile.snapshot_2024
      : profile && view === "series"
        ? profile.series_2021_2022[2022]
        : null;
  const previous =
    profile && view === "series" ? profile.series_2021_2022[2021] : null;
  const nationalTotal =
    current && meta
      ? (meta.national.dinese[String(current.year)]?.total ?? 0)
      : 0;

  const legalLabels = meta
    ? view === "2024"
      ? meta.legal_categories["2024"]
      : meta.legal_categories["series"]
    : [];

  return (
    <div className="flex min-h-screen flex-col">
      <AppHeader view={view} onViewChange={setView} />
      <main className="mx-auto w-full max-w-[1180px] flex-1 px-5 py-2 lg:px-8">
        <Intro />

        {error ? (
          <LoadError message={error} />
        ) : !meta || !territories ? (
          <LoadingSkeleton />
        ) : (
          <div className="space-y-5">
            <TerritoryPicker
              departments={territories.departments}
              municipalities={territories.municipalities}
              departmentCode={effectiveDepartmentCode}
              municipalityCode={effectiveMunicipalityCode}
              onDepartmentChange={handleDepartmentChange}
              onMunicipalityChange={handleMunicipalityChange}
            />

            {notice ? (
              <NoticeBanner
                notice={notice}
                onOpenDetails={() => setSourcesOpen(true)}
              />
            ) : null}

            {profileError ? (
              <Alert className="border-destructive/30 bg-card">
                <AlertTriangle className="text-destructive" />
                <AlertTitle>No se pudo cargar la ficha municipal</AlertTitle>
                <AlertDescription>{profileError}</AlertDescription>
              </Alert>
            ) : loading || !profile || !current || !municipality ? (
              <LoadingSkeleton />
            ) : (
              <>
                <div className="flex flex-wrap items-end justify-between gap-2 pt-1">
                  <div>
                    <h2 className="text-[1.35rem] font-semibold leading-tight tracking-tight">
                      {municipality.name}
                    </h2>
                    <p className="mt-0.5 text-[12.5px] text-muted-foreground">
                      {municipality.department_name} · Código{" "}
                      <span className="font-mono">{municipality.code}</span>
                    </p>
                  </div>
                </div>

                <KpiCards
                  view={view}
                  profile={profile}
                  municipality={municipality}
                  current={current}
                  previous={previous}
                  nationalTotal={nationalTotal}
                />

                <div className="grid gap-4 lg:grid-cols-12">
                  <div className="min-w-0 lg:col-span-7">
                    <PopulationCard population={profile.population} />
                  </div>
                  <div className="min-w-0 lg:col-span-5">
                    <SizeCard
                      view={view}
                      sizes={meta.size_order}
                      current={current}
                      previous={previous}
                    />
                  </div>
                  <div className="min-w-0 lg:col-span-8">
                    <CiiuCard
                      view={view}
                      sections={meta.ciiu_sections}
                      current={current}
                      previous={previous}
                    />
                  </div>
                  <div className="min-w-0 lg:col-span-4">
                    <LegalCard
                      view={view}
                      labels={legalLabels}
                      shortLabels={meta.legal_short_labels}
                      current={current}
                      previous={previous}
                      categories={{
                        current: Object.keys(current.legal).length,
                        previous: previous
                          ? Object.keys(previous.legal).length
                          : undefined,
                      }}
                    />
                  </div>
                  <div className="min-w-0 lg:col-span-12">
                    <PlacesCard
                      places={profile.places}
                      municipalityName={profile.name}
                      national={{
                        total: meta.coverage.places_total,
                        union: meta.coverage.places_excluded_union,
                        suffix999: meta.coverage.places_excluded_suffix_999,
                        missing:
                          meta.coverage.places_excluded_missing_coordinates,
                      }}
                    />
                  </div>
                </div>
              </>
            )}

            <SourcesDialog
              meta={meta}
              open={sourcesOpen}
              onOpenChange={setSourcesOpen}
            />
          </div>
        )}
      </main>

      <footer className="mt-10 border-t border-border/60">
        <div className="mx-auto flex max-w-[1180px] flex-col gap-3 px-5 py-6 text-[12px] text-muted-foreground sm:flex-row sm:items-center sm:justify-between lg:px-8">
          <p>
            Fuente: INE · Censo 2018 y DINESE. Conteos agregados, sin
            identificadores de empresa ni empleo.
          </p>
          <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
            <button
              type="button"
              onClick={() => setSourcesOpen(true)}
              className="inline-flex items-center gap-1 font-medium text-primary underline-offset-4 hover:underline"
            >
              Fuentes y metodología
              <ExternalLink className="size-3" />
            </button>
            <span>Datatón INE 2026</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

function PageFallback() {
  return (
    <div className="flex min-h-screen flex-col">
      <AppHeader view="2024" onViewChange={() => undefined} />
      <main className="mx-auto w-full max-w-[1180px] flex-1 px-5 py-2 lg:px-8">
        <Intro />
        <LoadingSkeleton />
      </main>
    </div>
  );
}

export default function HomePage() {
  return (
    <Suspense fallback={<PageFallback />}>
      <HomePageContent />
    </Suspense>
  );
}
