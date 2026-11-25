"use client";

import { useMemo, useState } from "react";
import {
  ChevronLeft,
  ChevronRight,
  Map as MapIcon,
  MapPinOff,
  Search,
  ShieldCheck,
} from "lucide-react";
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { fmt } from "@/lib/format";
import type { Place, Places } from "@/lib/types";

const PAGE_SIZE = 6;
const MAP_WIDTH = 680;
const MAP_HEIGHT = 380;
const MAP_PADDING = 36;

type StatusFilter = "all" | "map" | "excluded";

interface PlacesCardProps {
  places: Places;
  municipalityName: string;
  national: {
    suffix999: number;
    missing: number;
    union: number;
    total: number;
  };
}

function normalize(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function reasonLabel(place: Place): string {
  if (place.reasons.includes("sufijo_999")) return "Sufijo 999";
  if (place.reasons.includes("sin_coordenadas")) return "Sin coordenadas";
  return "Excluido";
}

function PlacesMap({ items }: { items: Place[] }) {
  const points = useMemo(
    () =>
      items.filter(
        (place) =>
          !place.excluded &&
          place.lon !== null &&
          place.lat !== null &&
          Number.isFinite(place.lon) &&
          Number.isFinite(place.lat),
      ),
    [items],
  );

  const projected = useMemo(() => {
    if (!points.length) return null;
    let minLon = Math.min(...points.map((point) => point.lon as number));
    let maxLon = Math.max(...points.map((point) => point.lon as number));
    let minLat = Math.min(...points.map((point) => point.lat as number));
    let maxLat = Math.max(...points.map((point) => point.lat as number));

    if (maxLon - minLon < 0.0001) {
      minLon -= 0.005;
      maxLon += 0.005;
    }
    if (maxLat - minLat < 0.0001) {
      minLat -= 0.005;
      maxLat += 0.005;
    }

    const meanLat = (minLat + maxLat) / 2;
    const aspect =
      ((maxLon - minLon) * Math.cos((meanLat * Math.PI) / 180)) /
      (maxLat - minLat);
    const maxWidth = MAP_WIDTH - MAP_PADDING * 2;
    const maxHeight = MAP_HEIGHT - MAP_PADDING * 2;
    let width = maxWidth;
    let height = width / aspect;
    if (height > maxHeight) {
      height = maxHeight;
      width = height * aspect;
    }
    const offsetX = (MAP_WIDTH - width) / 2;
    const offsetY = (MAP_HEIGHT - height) / 2;

    return points.map((point) => ({
      ...point,
      x:
        offsetX +
        (((point.lon as number) - minLon) / (maxLon - minLon)) * width,
      y:
        offsetY +
        ((maxLat - (point.lat as number)) / (maxLat - minLat)) * height,
    }));
  }, [points]);

  return (
    <div className="relative flex min-h-[320px] overflow-hidden rounded-xl border border-border/70 map-surface">
      <div className="pointer-events-none absolute left-3 top-3 z-10">
        <Badge
          variant="secondary"
          className="h-6 gap-1 rounded-full bg-white/90 px-2.5 text-[11px] backdrop-blur"
        >
          <MapIcon className="size-3" />
          {fmt(points.length)} puntos
        </Badge>
      </div>

      {projected ? (
        <svg
          viewBox={`0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`}
          className="my-auto block h-auto w-full"
          role="img"
          aria-label={`Mapa de ${points.length} lugares poblados con coordenadas`}
        >
          <defs>
            <pattern
              id="places-grid"
              width="36"
              height="36"
              patternUnits="userSpaceOnUse"
            >
              <path
                d="M 36 0 L 0 0 0 36"
                fill="none"
                stroke="var(--border)"
                strokeWidth="0.6"
                opacity="0.5"
              />
            </pattern>
          </defs>
          <rect width={MAP_WIDTH} height={MAP_HEIGHT} fill="url(#places-grid)" />
          {projected.map((point) => (
            <g key={point.code}>
              <circle
                cx={point.x}
                cy={point.y}
                r={10.5}
                fill="var(--primary)"
                opacity="0.08"
              />
              <circle
                cx={point.x}
                cy={point.y}
                r={4.1}
                fill="var(--primary)"
                stroke="var(--card)"
                strokeWidth="0.9"
              >
                <title>
                  {`${point.name} · ${(point.lat as number).toFixed(5)}, ${(point.lon as number).toFixed(5)}`}
                </title>
              </circle>
            </g>
          ))}
          <g transform={`translate(${MAP_WIDTH - 34} 34)`}>
            <circle r="13" fill="var(--card)" stroke="var(--border)" />
            <path d="M0 -8 L3.5 5 L0 2.5 L-3.5 5 Z" fill="var(--primary)" />
          </g>
        </svg>
      ) : (
        <div className="flex w-full flex-col items-center justify-center gap-2 text-center">
          <MapPinOff className="size-6 text-muted-foreground/60" />
          <p className="text-sm font-medium">Sin puntos para mapear</p>
          <p className="max-w-[240px] text-xs text-muted-foreground">
            Todos los lugares de este municipio están excluidos por sufijo 999
            o por falta de coordenadas.
          </p>
        </div>
      )}
    </div>
  );
}

export function PlacesCard({
  places,
  municipalityName,
  national,
}: PlacesCardProps) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<StatusFilter>("all");
  const [page, setPage] = useState(1);

  const normalizedQuery = normalize(query);

  const filtered = useMemo(
    () =>
      places.items.filter((place) => {
        if (normalizedQuery && !normalize(place.name).includes(normalizedQuery)) {
          return false;
        }
        if (status === "map" && place.excluded) return false;
        if (status === "excluded" && !place.excluded) return false;
        return true;
      }),
    [places.items, normalizedQuery, status],
  );

  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const safePage = Math.min(page, pageCount);
  const start = (safePage - 1) * PAGE_SIZE;
  const visible = filtered.slice(start, start + PAGE_SIZE);

  return (
    <Card className="shadow-sm">
      <CardContent className="space-y-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold tracking-tight">
              Lugares poblados
            </h2>
            <p className="mt-0.5 text-[13px] text-muted-foreground">
              Centroides del Censo 2018 en {municipalityName}. No son
              direcciones de empresas.
            </p>
          </div>
          <p className="text-[12px] text-muted-foreground">
            <span className="font-medium text-foreground">
              {fmt(places.map_points)}
            </span>{" "}
            en mapa ·{" "}
            <span className="font-medium text-foreground">
              {fmt(places.excluded.union)}
            </span>{" "}
            excluidos
          </p>
        </div>

        <div className="grid gap-4 lg:grid-cols-[0.95fr_1.05fr]">
          <PlacesMap items={places.items} />

          <div className="flex min-w-0 flex-col gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <div className="relative min-w-[180px] flex-1">
                <Search className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={query}
                  onChange={(event) => {
                    setQuery(event.target.value);
                    setPage(1);
                  }}
                  placeholder="Buscar lugar poblado…"
                  aria-label="Buscar lugar poblado"
                  className="h-9 rounded-lg border-border pl-8 text-[12.5px]"
                />
              </div>
              <Select
                value={status}
                onValueChange={(value) => {
                  if (typeof value === "string") {
                    setStatus(value as StatusFilter);
                    setPage(1);
                  }
                }}
                items={{ all: "Todos", map: "En mapa", excluded: "Excluidos" }}
              >
                <SelectTrigger
                  aria-label="Filtrar por estado"
                  className="h-9 w-[128px] rounded-lg border-border text-[12.5px]"
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos</SelectItem>
                  <SelectItem value="map">En mapa</SelectItem>
                  <SelectItem value="excluded">Excluidos</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="overflow-hidden rounded-lg border">
              <Table>
                <TableHeader>
                  <TableRow className="bg-secondary/45 hover:bg-secondary/45">
                    <TableHead className="h-9 text-[11.5px]">Lugar</TableHead>
                    <TableHead className="h-9 text-right text-[11px]">
                      Coordenadas
                    </TableHead>
                    <TableHead className="h-9 text-[11.5px]">Estado</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {visible.length ? (
                    visible.map((place) => (
                      <TableRow key={place.code} className="text-[12.5px]">
                        <TableCell className="max-w-[190px] truncate font-medium">
                          {place.name}
                        </TableCell>
                        <TableCell className="text-right font-mono text-[11.5px] tabular-nums text-muted-foreground">
                          {place.lon === null || place.lat === null
                            ? "—"
                            : `${place.lat.toFixed(4)}, ${place.lon.toFixed(4)}`}
                        </TableCell>
                        <TableCell>
                          {place.excluded ? (
                            <Badge
                              variant="outline"
                              className="h-5 rounded-full border-amber-200 bg-amber-50 px-2 text-[10px] font-medium text-amber-900"
                            >
                              {reasonLabel(place)}
                            </Badge>
                          ) : (
                            <Badge
                              variant="outline"
                              className="h-5 rounded-full border-teal-200 bg-teal-50 px-2 text-[10px] font-medium text-teal-900"
                            >
                              En mapa
                            </Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    ))
                  ) : (
                    <TableRow>
                      <TableCell
                        colSpan={3}
                        className="h-24 text-center text-xs text-muted-foreground"
                      >
                        No hay lugares que coincidan con el filtro.
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </div>

            <div className="flex items-center justify-between gap-2 text-[11.5px] text-muted-foreground">
              <span>
                {filtered.length
                  ? `${fmt(start + 1)}–${fmt(Math.min(start + PAGE_SIZE, filtered.length))} de ${fmt(filtered.length)}`
                  : "0 resultados"}
              </span>
              <div className="flex items-center gap-1">
                <Button
                  variant="outline"
                  size="icon"
                  className="size-7 rounded-md"
                  onClick={() => setPage((current) => Math.max(1, current - 1))}
                  disabled={safePage <= 1}
                  aria-label="Página anterior"
                >
                  <ChevronLeft className="size-3.5" />
                </Button>
                <span className="min-w-12 text-center font-mono text-[10.5px]">
                  {safePage} / {pageCount}
                </span>
                <Button
                  variant="outline"
                  size="icon"
                  className="size-7 rounded-md"
                  onClick={() =>
                    setPage((current) => Math.min(pageCount, current + 1))
                  }
                  disabled={safePage >= pageCount}
                  aria-label="Página siguiente"
                >
                  <ChevronRight className="size-3.5" />
                </Button>
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-start gap-2 rounded-lg bg-secondary/40 px-3 py-2 text-[12px] leading-relaxed text-muted-foreground">
          <ShieldCheck className="mt-0.5 size-3.5 shrink-0 text-primary" />
          <span>
            Se excluyen del mapa los lugares con sufijo 999 y sin coordenadas.
            En el país: {fmt(national.suffix999)} con sufijo 999 y{" "}
            {fmt(national.missing)} sin coordenadas. En este municipio:{" "}
            {fmt(places.excluded.suffix_999)} y{" "}
            {fmt(places.excluded.missing_coordinates)}. La tabla los conserva.
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
