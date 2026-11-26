import * as React from "react";

import { cn } from "@/lib/utils";

const fieldClass =
  "flex w-full rounded-md border border-line bg-white px-3 py-2 text-[15px] text-ink shadow-[0_1px_1px_rgba(16,32,52,.03)] transition-colors placeholder:text-muted/70 hover:border-[#bfbfbf] focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/25 disabled:cursor-not-allowed disabled:bg-surface";

export function Input({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn(fieldClass, "h-10", className)} {...props} />;
}

export function Textarea({
  className,
  ...props
}: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={cn(fieldClass, "min-h-[88px] resize-y", className)} {...props} />;
}

export function Label({ className, ...props }: React.LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      className={cn("mb-1.5 block text-[14px] font-semibold text-ink", className)}
      {...props}
    />
  );
}

export function FieldHint({
  className,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn("mt-1 text-[13px] leading-snug text-muted", className)} {...props} />;
}

export function FieldError({
  className,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return <p className={cn("mt-1 text-[13px] font-medium text-fail", className)} {...props} />;
}

export function Checkbox({
  className,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      type="checkbox"
      className={cn(
        "h-4 w-4 rounded border-line text-brand accent-[#004080] focus:ring-2 focus:ring-accent/30",
        className,
      )}
      {...props}
    />
  );
}
