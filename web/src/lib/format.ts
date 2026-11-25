export const MONTH_NAMES = [
  "Enero",
  "Febrero",
  "Marzo",
  "Abril",
  "Mayo",
  "Junio",
  "Julio",
  "Agosto",
  "Septiembre",
  "Octubre",
  "Noviembre",
  "Diciembre",
] as const;

export const MONTH_ABBR = [
  "ene",
  "feb",
  "mar",
  "abr",
  "may",
  "jun",
  "jul",
  "ago",
  "sep",
  "oct",
  "nov",
  "dic",
] as const;

/**
 * Formato numérico determinista equivalente a es-GT (1,234.56).
 * Se evita Intl para que servidor y navegador rendericen idéntico.
 */
export function formatNumber(value: number, decimals = 0): string {
  if (!Number.isFinite(value)) return "—";
  const safe = Math.abs(value) < 0.5 * 10 ** -decimals ? 0 : value;
  const fixed = Math.abs(safe).toFixed(decimals);
  const [integer, fraction] = fixed.split(".");
  const grouped = integer.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  const sign = safe < 0 ? "-" : "";
  return `${sign}${grouped}${fraction ? `.${fraction}` : ""}`;
}

export function formatQuetzales(value: number, decimals = 2): string {
  return `Q ${formatNumber(value, decimals)}`;
}

export function formatSignedPercent(value: number, decimals = 2): string {
  if (!Number.isFinite(value)) return "—";
  const rounded = Number(value.toFixed(decimals));
  const sign = rounded > 0 ? "+" : rounded < 0 ? "−" : "";
  return `${sign}${formatNumber(Math.abs(rounded), decimals)} %`;
}

export function formatKcal(value: number, decimals = 0): string {
  return `${formatNumber(value, decimals)} kcal`;
}

export function formatUnitQuantity(quantity: number, unit: string): string {
  const normalized = unit.trim().toLowerCase();
  const decimals = Number.isInteger(quantity) ? 0 : 1;
  if (normalized.startsWith("gramo")) {
    return `${formatNumber(quantity, decimals)} g`;
  }
  if (normalized.startsWith("mililitro")) {
    return `${formatNumber(quantity, decimals)} ml`;
  }
  return `${formatNumber(quantity, decimals)} ${normalized}`;
}

export function formatUtcStamp(iso: string | null): string {
  if (!iso) return "sin registro de descarga";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  const day = String(date.getUTCDate()).padStart(2, "0");
  const month = MONTH_ABBR[date.getUTCMonth()];
  const year = date.getUTCFullYear();
  const hours = String(date.getUTCHours()).padStart(2, "0");
  const minutes = String(date.getUTCMinutes()).padStart(2, "0");
  return `${day} ${month} ${year} · ${hours}:${minutes} UTC`;
}

export function formatFileSize(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${formatNumber(bytes / (1024 * 1024), 1)} MB`;
  return `${formatNumber(bytes / 1024, 1)} KB`;
}

const GROUP_SHORT_NAMES: Record<string, string> = {
  "Vegetales (verduras u hortalizas)": "Vegetales",
  "Carnes, Aves, Pescados y Huevos": "Carnes y huevos",
  "Leche y productos lácteos": "Lácteos",
  "Productos alimenticios N.E.P.": "Otros alimentos",
  "Comidas y bebidas fuera del hogar": "Comidas fuera de casa",
  "Bebidas no alcohólicas": "Bebidas",
  Azucares: "Azúcares",
};

export function shortGroupName(name: string): string {
  return GROUP_SHORT_NAMES[name] ?? name;
}

