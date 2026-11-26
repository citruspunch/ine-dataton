import * as React from "react";

import { cn } from "@/lib/utils";

export function DataRow({
  label,
  children,
  className,
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "grid grid-cols-1 gap-0.5 border-b border-line px-4 py-2.5 last:border-0 sm:grid-cols-[190px_1fr] sm:gap-4",
        className,
      )}
    >
      <dt className="text-[13px] font-semibold text-muted sm:pt-0.5">
        {label}
      </dt>
      <dd className="min-w-0 text-[14.5px] text-ink">{children}</dd>
    </div>
  );
}

export function DataList({
  className,
  ...props
}: React.HTMLAttributes<HTMLDListElement>) {
  return (
    <dl
      className={cn("overflow-hidden rounded-lg border border-line bg-white", className)}
      {...props}
    />
  );
}
