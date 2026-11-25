import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPct(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  const text = value.toFixed(2);
  return `${value > 0 ? "+" : ""}${text.replace(".", ",")}%`;
}
