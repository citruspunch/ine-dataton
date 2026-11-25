import { cn } from "cn";

export function BrandMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 48 48"
      className={cn("size-11 shrink-0", className)}
      aria-hidden="true"
    >
      <rect width="48" height="48" rx="14" fill="var(--primary)" />
      <path
        d="M11 34V22.5L17.5 28L24 15L30.5 27L37 20.5V34H11Z"
        fill="var(--primary-foreground)"
        opacity="0.94"
      />
      <circle cx="37" cy="12.5" r="3.5" fill="var(--chart-2)" />
      <path
        d="M11 37H37"
        stroke="var(--primary-foreground)"
        strokeWidth="1.6"
        strokeLinecap="round"
        opacity="0.55"
      />
    </svg>
  );
}
