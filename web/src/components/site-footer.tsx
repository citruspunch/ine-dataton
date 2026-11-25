import Link from "next/link";
import { Landmark } from "lucide-react";

export function SiteFooter() {
  return (
    <footer className="border-t border-border/60 bg-card/40">
      <div className="mx-auto flex max-w-6xl flex-col gap-2 px-4 py-8 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
        <div className="flex items-center gap-2 text-sm text-foreground">
          <span className="grid size-6 place-items-center rounded bg-primary text-primary-foreground">
            <Landmark className="size-3" aria-hidden />
          </span>
          <span className="font-heading font-semibold">Mesa de Precios</span>
          <span className="text-muted-foreground">· Datos del INE</span>
        </div>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
          <Link href="/fuentes" className="hover:text-foreground">
            Fuentes y método
          </Link>
          <a href="https://datos.ine.gob.gt" target="_blank" rel="noreferrer" className="hover:text-foreground">
            datos.ine.gob.gt
          </a>
          <span>Uso informativo</span>
        </div>
      </div>
    </footer>
  );
}
