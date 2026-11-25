import type { IndicatorFormat, PressureClass } from "@/lib/types";

const integerFormatter = new Intl.NumberFormat("es-GT", {
  maximumFractionDigits: 0,
});

const decimalFormatter = new Intl.NumberFormat("es-GT", {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

const twoDecimalFormatter = new Intl.NumberFormat("es-GT", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

export function formatInteger(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return integerFormatter.format(value);
}

export function formatPercent(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const formatter =
    digits === 2 ? twoDecimalFormatter : digits === 1 ? decimalFormatter : integerFormatter;
  return `${formatter.format(value)}%`;
}

export function formatRatio(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return (digits === 2 ? twoDecimalFormatter : decimalFormatter).format(value);
}

export function formatCurrency(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const formatter = digits === 0 ? integerFormatter : digits === 1 ? decimalFormatter : twoDecimalFormatter;
  return `Q${formatter.format(value)}`;
}

export function formatIndex(value: number | null | undefined): string {
  return formatRatio(value, 2);
}

export function formatIndicatorValue(
  value: number | null | undefined,
  format: IndicatorFormat,
): string {
  switch (format) {
    case "percent":
      return formatPercent(value);
    case "currency":
      return formatCurrency(value);
    case "integer":
      return formatInteger(value);
    case "index":
      return formatIndex(value);
    case "ratio":
    default:
      return formatRatio(value);
  }
}

export function formatCompactCurrency(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const billions = value / 1_000_000_000;
  if (Math.abs(billions) >= 0.1) {
    return `Q${twoDecimalFormatter.format(billions)} mil M`;
  }
  const millions = value / 1_000_000;
  return `Q${decimalFormatter.format(millions)} M`;
}

export function formatBytes(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  if (value >= 1_000_000) return `${decimalFormatter.format(value / 1_000_000)} MB`;
  if (value >= 1_000) return `${integerFormatter.format(value / 1_000)} KB`;
  return `${integerFormatter.format(value)} B`;
}

export function formatUtc(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return `${new Intl.DateTimeFormat("es-GT", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(date)} UTC`;
}

export function formatDateUtc(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return `${new Intl.DateTimeFormat("es-GT", {
    dateStyle: "medium",
    timeZone: "UTC",
  }).format(date)} UTC`;
}

export function normalizeSearch(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

export const PRESSURE_CLASS_STYLES: Record<
  PressureClass,
  { label: string; badge: string; bar: string; dot: string }
> = {
  alta: {
    label: "Presión alta",
    badge: "border-red-200 bg-red-50 text-red-800 dark:border-red-900/60 dark:bg-red-950/40 dark:text-red-200",
    bar: "#b91c1c",
    dot: "bg-red-700",
  },
  media_alta: {
    label: "Presión media-alta",
    badge:
      "border-orange-200 bg-orange-50 text-orange-900 dark:border-orange-900/60 dark:bg-orange-950/40 dark:text-orange-200",
    bar: "#c2410c",
    dot: "bg-orange-600",
  },
  media: {
    label: "Presión media",
    badge:
      "border-amber-200 bg-amber-50 text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-200",
    bar: "#a16207",
    dot: "bg-amber-600",
  },
  baja: {
    label: "Presión baja",
    badge:
      "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-200",
    bar: "#15803d",
    dot: "bg-emerald-700",
  },
  sin_dato: {
    label: "Sin dato",
    badge: "border-border bg-muted text-muted-foreground",
    bar: "#64748b",
    dot: "bg-slate-500",
  },
};

export function pressureLabel(value: PressureClass | null | undefined): string {
  return value ? PRESSURE_CLASS_STYLES[value]?.label ?? "Sin dato" : "Sin dato";
}

export function licenseBadgeClass(licenseId: string, nonCommercial: boolean): string {
  if (nonCommercial || licenseId === "cc-nc") {
    return "border-rose-300 bg-rose-50 text-rose-800 dark:border-rose-900/60 dark:bg-rose-950/40 dark:text-rose-200";
  }
  if (licenseId === "cc-zero") {
    return "border-emerald-300 bg-emerald-50 text-emerald-800 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-200";
  }
  if (licenseId === "odc-by" || licenseId === "cc-by") {
    return "border-sky-300 bg-sky-50 text-sky-800 dark:border-sky-900/60 dark:bg-sky-950/40 dark:text-sky-200";
  }
  return "border-border bg-muted text-muted-foreground";
}
