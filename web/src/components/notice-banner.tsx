"use client";

import { Info, TriangleAlert } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import type { Notice } from "@/lib/types";
import { cn } from "@/lib/utils";

export function NoticeBanner({
  notice,
  onOpenDetails,
}: {
  notice: Notice;
  onOpenDetails?: () => void;
}) {
  const isWarning = notice.severity === "warning";
  const Icon = isWarning ? TriangleAlert : Info;

  return (
    <Alert
      className={cn(
        "items-start gap-x-3 rounded-xl border px-4 py-3.5",
        isWarning
          ? "border-amber-300/70 bg-amber-50/60 text-amber-950"
          : "border-teal-300/60 bg-teal-50/50 text-teal-950",
      )}
    >
      <Icon
        className={cn(
          "mt-0.5 size-4",
          isWarning ? "text-amber-700" : "text-teal-700",
        )}
      />
      <AlertTitle className="space-y-2 text-sm font-semibold">
        <div className="hidden flex-wrap items-center gap-1.5 sm:flex">
          {notice.badges.map((badge) => (
            <Badge
              key={badge}
              variant="outline"
              className={cn(
                "h-5 rounded-full px-2 text-[11px] font-medium",
                isWarning
                  ? "border-amber-300/80 bg-white/70 text-amber-900"
                  : "border-teal-300/80 bg-white/70 text-teal-900",
              )}
            >
              {badge}
            </Badge>
          ))}
        </div>
        <Badge
          variant="outline"
          className={cn(
            "h-5 w-fit rounded-full px-2 text-[10px] font-medium sm:hidden",
            isWarning
              ? "border-amber-300/80 bg-white/70 text-amber-900"
              : "border-teal-300/80 bg-white/70 text-teal-900",
          )}
        >
          {notice.badges.join(" · ")}
        </Badge>
        <span>
          {isWarning
            ? "Corte 2024: no comparable con la serie"
            : "Serie 2021–2022: comparable solo entre esos años"}
        </span>
      </AlertTitle>
      <AlertDescription
        className={cn(
          "mt-1 text-[13px] leading-relaxed",
          isWarning ? "text-amber-900/85" : "text-teal-900/85",
        )}
      >
        {isWarning
          ? "El salto frente a 2021 refleja cambios de cobertura y de personería, no crecimiento económico. No compares esta vista con la serie 2021–2022. "
          : "La serie permite leer 2021 y 2022 entre sí, pero no debe extenderse a 2024. "}
        {onOpenDetails ? (
          <button
            type="button"
            onClick={onOpenDetails}
            className="font-medium underline decoration-current/40 underline-offset-2 hover:decoration-current"
          >
            Ver metodología
          </button>
        ) : null}
      </AlertDescription>
    </Alert>
  );
}
