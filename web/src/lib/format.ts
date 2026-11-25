import type { MetricStats, RecordItem, SourceGroup } from "./types";

const MONTHS_SHORT = [
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
];

const MONTHS_LONG = [
  "enero",
  "febrero",
  "marzo",
  "abril",
  "mayo",
  "junio",
  "julio",
  "agosto",
  "septiembre",
  "octubre",
  "noviembre",
  "diciembre",
];

/**
 * Deterministic es-GT number formatting. We intentionally avoid `Intl` here:
 * Node and the browser can ship different CLDR data, which produces hydration
 * text mismatches. Prices in these files use comma thousands and dot decimals.
 */
export function formatNumber(value: number | null | undefined, maximumFractionDigits = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const negative = value < 0;
  const absolute = Math.abs(value);
  const fixed = absolute.toFixed(maximumFractionDigits);
  const [integerPart, decimalPart = ""] = fixed.split(".");
  const trimmedDecimal = decimalPart.replace(/0+$/, "");
  const grouped = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  const text = trimmedDecimal ? `${grouped}.${trimmedDecimal}` : grouped;
  return negative ? `-${text}` : text;
}

export function formatCompact(value: number): string {
  return formatNumber(value, 0);
}

export function formatPrice(value: number | null | undefined): string {
  return formatNumber(value, 2);
}

export function formatPercent(value: number): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${formatNumber(value, 1)}%`;
}

function isoParts(iso: string): { year: number; month: number; day: number } | null {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso);
  if (!match) return null;
  return { year: Number(match[1]), month: Number(match[2]), day: Number(match[3]) };
}

function capitalize(value: string): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

export function formatDate(
  iso: string | null | undefined,
  granularity: "day" | "month" = "day",
): string {
  if (!iso) return "Sin fecha";
  const parts = isoParts(iso);
  if (!parts) return iso;
  if (granularity === "month") {
    return `${capitalize(MONTHS_LONG[parts.month - 1] ?? "")} de ${parts.year}`;
  }
  return `${String(parts.day).padStart(2, "0")} ${MONTHS_SHORT[parts.month - 1] ?? ""} ${parts.year}`;
}

export function formatShortDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const parts = isoParts(iso);
  if (!parts) return iso;
  return `${String(parts.day).padStart(2, "0")}/${String(parts.month).padStart(2, "0")}/${parts.year}`;
}

export function formatUtc(iso: string | null | undefined): string {
  if (!iso) return "No registrado";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  const day = String(date.getUTCDate()).padStart(2, "0");
  const month = MONTHS_SHORT[date.getUTCMonth()];
  const year = date.getUTCFullYear();
  const hours = String(date.getUTCHours()).padStart(2, "0");
  const minutes = String(date.getUTCMinutes()).padStart(2, "0");
  return `${day} ${month} ${year}, ${hours}:${minutes} UTC`;
}

export function formatSha(sha: string | null | undefined, length = 16): string {
  if (!sha) return "No registrado";
  return sha.length > length ? `${sha.slice(0, length)}…` : sha;
}

export function parsePriceInput(raw: string): number | null {
  let text = raw.trim().replace(/\u00a0/g, "").replace(/\s/g, "");
  if (!text) return null;
  text = text.replace(/[Qq$]/g, "").replace(/[^0-9,.\-]/g, "");
  if (!text || text === "-") return null;
  const hasComma = text.includes(",");
  const hasDot = text.includes(".");
  if (hasComma && hasDot) {
    const lastComma = text.lastIndexOf(",");
    const lastDot = text.lastIndexOf(".");
    text =
      lastComma > lastDot
        ? text.replace(/\./g, "").replace(",", ".")
        : text.replace(/,/g, "");
  } else if (hasComma) {
    const parts = text.split(",");
    if (parts.length === 2) {
      const [left, right] = parts;
      if (
        /^\d+$/.test(right) &&
        right.length === 3 &&
        left.replace("-", "").length >= 1 &&
        left.replace("-", "").length <= 3 &&
        left.replace("-", "") !== "0"
      ) {
        text = text.replace(",", "");
      } else {
        text = text.replace(",", ".");
      }
    } else {
      text = parts.every((part) => /^\d+$/.test(part) && part.length === 3)
        ? text.replace(/,/g, "")
        : "";
    }
  }
  const value = Number(text);
  return Number.isFinite(value) ? value : null;
}

export function statusTone(status: string): "success" | "warning" | "info" | "neutral" {
  if (status === "current") return "success";
  if (status === "frozen") return "warning";
  if (status === "limited") return "info";
  return "neutral";
}

export function statusLabel(status: string): string {
  if (status === "current") return "Actualizado";
  if (status === "frozen") return "Congelado";
  if (status === "limited") return "Cobertura parcial";
  return "Sin estado";
}

export function flagLabel(flag: string): string {
  switch (flag) {
    case "invalid_date":
      return "Fecha inválida";
    case "missing_date":
      return "Sin fecha";
    case "duplicate":
      return "Duplicado";
    case "thousands_comma":
      return "Comas";
    case "missing_nog":
      return "Sin NOG";
    case "missing_value":
      return "Sin precio";
    case "missing_product":
      return "Sin producto";
    default:
      return flag;
  }
}

export function flagDescription(flag: string): string {
  switch (flag) {
    case "invalid_date":
      return "La fecha original no es una fecha calendario válida; el registro se muestra pero no entra en los resúmenes.";
    case "missing_date":
      return "No hay fecha de referencia; el registro se muestra pero no entra en los resúmenes.";
    case "duplicate":
      return "Observación repetida. Se conserva la copia más reciente y esta se excluye de los cálculos.";
    case "thousands_comma":
      return "El precio venía con separador de miles; se convirtió correctamente antes de calcular.";
    case "missing_nog":
      return "El registro no tiene número de operación gubernamental (NOG).";
    case "missing_value":
      return "No hay un precio o índice numérico utilizable.";
    case "missing_product":
      return "El nombre del producto o material está vacío.";
    default:
      return flag;
  }
}

export function recordStatus(record: RecordItem): string {
  return record.status;
}

export function sourceName(group: SourceGroup): string {
  if (group === "DPIR") return "Precios de Referencia";
  if (group === "IPMC") return "Materiales de construcción";
  if (group === "ICC") return "Costo de construcción";
  return "Canastas básicas";
}

export function metricUnitLabel(stats: MetricStats | null): string {
  if (!stats) return "—";
  if (stats.valueKind === "price") return stats.currency === "GTQ" ? "Q" : stats.unit;
  return stats.unit;
}

export function metricValueSuffix(stats: MetricStats | null): string {
  if (!stats) return "";
  if (stats.valueKind === "index") return "puntos de índice";
  if (stats.valueKind === "cost") return "Q por persona";
  return "Q";
}

export function safeText(value: string | null | undefined, fallback = "—"): string {
  return value && value.trim() ? value : fallback;
}

export function truncate(value: string, max = 90): string {
  if (value.length <= max) return value;
  return `${value.slice(0, max - 1).trimEnd()}…`;
}

export function formatBytes(bytes: number | null | undefined): string {
  if (!bytes) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

export function formatCutoffDate(
  iso: string | null | undefined,
  granularity: "day" | "month" = "day",
): string {
  if (!iso) return "Sin datos";
  return formatDate(iso, granularity);
}
