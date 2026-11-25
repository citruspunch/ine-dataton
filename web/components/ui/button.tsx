import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 rounded-md text-sm font-semibold transition-all focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "bg-brand text-white shadow-sm hover:bg-brand-dark active:translate-y-px",
        accent:
          "bg-[#0068d6] text-white shadow-sm hover:bg-[#0057b3] active:translate-y-px",
        secondary:
          "border border-line bg-white text-ink shadow-[0_1px_1px_rgba(16,32,52,.04)] hover:border-[#bfbfbf] hover:bg-surface",
        outline: "border border-brand/40 bg-transparent text-brand hover:bg-brand-soft",
        ghost: "text-brand hover:bg-brand-soft",
        danger: "bg-fail text-white shadow-sm hover:bg-[#662000]",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-8 px-3 text-[13px]",
        lg: "h-11 px-5",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return (
    <button className={cn(buttonVariants({ variant, size }), className)} {...props} />
  );
}

export { buttonVariants };
