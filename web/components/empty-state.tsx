import type { Icon } from "@phosphor-icons/react";

export function EmptyState({
  icon: Icon,
  title,
  children,
  action,
}: {
  icon: Icon;
  title: string;
  children?: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-[#c7c7c7] bg-white px-6 py-12 text-center">
      <span className="flex h-11 w-11 items-center justify-center rounded-full bg-brand-soft text-brand">
        <Icon className="h-5 w-5" aria-hidden weight="duotone" />
      </span>
      <div className="space-y-1">
        <p className="text-[16px] font-semibold text-ink">{title}</p>
        {children ? (
          <div className="mx-auto max-w-md text-[14px] leading-relaxed text-muted">
            {children}
          </div>
        ) : null}
      </div>
      {action ? <div className="pt-1">{action}</div> : null}
    </div>
  );
}
