import raw from "@/data/basket.json";

import type { Area, AreaData, AreaMonth, BasketData, IpcRow } from "./types";

/**
 * Artefacto estático generado por `uv run basket-ingest`.
 * La app no consulta servicios externos en tiempo de ejecución.
 */
export const basketData = raw as unknown as BasketData;

export const AREAS: Area[] = ["Urbana", "Rural"];

export function areaData(area: Area): AreaData {
  return basketData.areas[area];
}

export function areaSummary(area: Area) {
  return basketData.meta.areas[area];
}

export function findMonth(area: Area, period: string): AreaMonth {
  const month = areaData(area).months.find((item) => item.period === period);
  if (!month) {
    throw new Error(`No hay datos para ${area} en el periodo ${period}`);
  }
  return month;
}

export function findIpc(period: string): IpcRow {
  const row = basketData.ipc.find((item) => item.period === period);
  if (!row) {
    throw new Error(`No hay IPC para el periodo ${period}`);
  }
  return row;
}

export function availablePeriods(area: Area): string[] {
  return areaData(area).months.map((month) => month.period);
}

export function availableYears(area: Area): number[] {
  return Array.from(
    new Set(areaData(area).months.map((month) => month.year)),
  ).sort((a, b) => a - b);
}

export function monthsForYear(area: Area, year: number): number[] {
  return areaData(area)
    .months.filter((month) => month.year === year)
    .map((month) => month.month)
    .sort((a, b) => a - b);
}

export function latestPeriod(area: Area): string {
  const months = areaData(area).months;
  return months[months.length - 1].period;
}

export function lastDataUpdate(): string {
  const stamps = basketData.meta.sources
    .map((source) => source.downloaded_at_utc ?? source.verified_at_utc)
    .filter((value): value is string => Boolean(value))
    .sort();
  return stamps[stamps.length - 1] ?? basketData.meta.generatedAtUtc;
}
