import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { PRESSURE_CLASS_STYLES } from "@/lib/format";
import type { PressureClass } from "@/lib/types";

export function PressureBadge({
  value,
  className,
}: {
  value: PressureClass | null | undefined;
  className?: string;
}) {
  const style = value ? PRESSURE_CLASS_STYLES[value] : PRESSURE_CLASS_STYLES.sin_dato;
  return (
    <Badge
      variant="outline"
      className={cn("whitespace-nowrap px-2 py-0 text-[11px] font-medium", style.badge, className)}
    >
      <span className={cn("mr-1.5 inline-block size-1.5 rounded-full", style.dot)} />
      {style.label}
    </Badge>
  );
}

export function SuppressionBadge({
  fields,
  className,
}: {
  fields: string[];
  className?: string;
}) {
  if (!fields.length) return null;
  return (
    <Badge
      variant="outline"
      className={cn(
        "whitespace-nowrap border-dashed border-amber-300 bg-amber-50 font-mono text-[10px] text-amber-900 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-200",
        className,
      )}
      title={`Celda suprimida por secreto estadístico (conteo 1–4). Campos: ${fields.join(", ")}`}
    >
      § &lt;5
    </Badge>
  );
}
