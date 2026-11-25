import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const alertVariants = cva("flex gap-3 rounded-lg border px-4 py-3 text-sm", {
  variants: {
    variant: {
      info: "border-line bg-white text-ink",
      ok: "border-[#c9e68a] bg-ok-bg text-ok",
      warn: "border-[#ffe28a] bg-warn-bg text-warn",
      fail: "border-[#ffb699] bg-fail-bg text-fail",
    },
  },
  defaultVariants: { variant: "info" },
});

export interface AlertProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof alertVariants> {}

export function Alert({ className, variant, ...props }: AlertProps) {
  return <div role="status" className={cn(alertVariants({ variant }), className)} {...props} />;
}
