"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Consulta" },
  { href: "/review", label: "Revisión técnica" },
];

export function SiteHeader() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-white/95 backdrop-blur print:hidden">
      <div className="h-1 w-full bg-gradient-to-r from-brand via-accent to-brand" />
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-3 px-5 py-3 sm:px-6">
        <Link href="/" className="flex items-center gap-3" aria-label="INE Data Trust, inicio">
          <Image
            src="/ine-logo.png"
            alt="Instituto Nacional de Estadística"
            width={7026}
            height={2273}
            priority
            className="h-10 w-auto sm:h-11"
          />
          <span className="hidden border-l border-line pl-3 sm:block">
            <span className="block text-[13px] font-bold uppercase tracking-[0.18em] text-brand">
              Data Trust
            </span>
            <span className="block text-[11px] leading-tight text-muted">
              Validación técnica de agregados
            </span>
          </span>
        </Link>

        <nav
          className="flex w-full items-center justify-end gap-1 border-t border-line/70 pt-2 sm:ml-auto sm:w-auto sm:border-0 sm:pt-0"
          aria-label="Navegación principal"
        >
          {NAV.map((item) => {
            const active =
              item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "relative rounded-md px-3 py-2 text-[13.5px] font-semibold transition-colors",
                  active
                    ? "text-brand after:absolute after:inset-x-3 after:-bottom-[13px] after:h-0.5 after:rounded-full after:bg-accent"
                    : "text-muted hover:bg-brand-soft hover:text-brand",
                )}
              >
                {item.label}
              </Link>
            );
          })}
          <a
            href="https://www.ine.gob.gt"
            target="_blank"
            rel="noreferrer"
            className="ml-1 hidden items-center gap-1 rounded-md px-3 py-2 text-[13.5px] font-semibold text-muted transition-colors hover:bg-brand-soft hover:text-brand md:inline-flex"
          >
            ine.gob.gt
            <span aria-hidden className="text-[11px]">
              ↗
            </span>
          </a>
        </nav>
      </div>
    </header>
  );
}
