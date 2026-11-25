import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPct(value: number | null | undefined): string {
  if (value === null || value === undefined) return "Sin dato";
  const text = value.toFixed(2);
  return `${value > 0 ? "+" : ""}${text.replace(".", ",")}%`;
}

const numberFormat = new Intl.NumberFormat("es-GT", {
  maximumFractionDigits: 4,
  minimumFractionDigits: 0,
});

export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "Sin dato";
  return numberFormat.format(value);
}
