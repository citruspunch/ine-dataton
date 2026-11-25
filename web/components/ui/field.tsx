import * as React from "react";

import { cn } from "@/lib/utils";

const fieldClass =
  "w-full rounded border border-[#c3ccd8] bg-white px-2.5 py-2 text-sm text-ink placeholder:text-muted/70 focus:border-[#7fa3cc] focus:outline focus:outline-2 focus:outline-offset-1 focus:outline-[#9db9dd]";

export function Input({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn(fieldClass, className)} {...props} />;
}

export function Textarea({
  className,
  ...props
}: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={cn(fieldClass, "min-h-[80px] resize-y", className)} {...props} />;
}

export function Select({
  className,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={cn(fieldClass, "pr-8", className)} {...props} />;
}

export function Label({ className, ...props }: React.LabelHTMLAttributes<HTMLLabelElement>) {
  return (
    <label
      className={cn("mb-1 block text-[12.5px] font-semibold text-muted", className)}
      {...props}
    />
  );
}
