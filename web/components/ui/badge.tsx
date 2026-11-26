import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2.5 py-0.5 text-[12.5px] font-semibold leading-5",
  {
    variants: {
      variant: {
        default: "bg-none-bg text-none",
        ok: "bg-ok-bg text-ok",
        warn: "bg-warn-bg text-warn",
        fail: "bg-fail-bg text-fail",
        none: "bg-none-bg text-none",
        syn: "bg-syn-bg text-syn",
        info: "bg-brand-soft text-brand",
        accent: "bg-accent-soft text-[#004080]",
        outline: "border border-line bg-white text-muted",
      },
    },
    defaultVariants: { variant: "default" },
  },
);

export interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
