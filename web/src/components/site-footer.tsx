import { Database, ExternalLink } from "lucide-react";

export function SiteFooter() {
  return (
    <footer className="border-t border-border/70 bg-card/50">
      <div className="mx-auto grid max-w-7xl gap-6 px-4 py-10 sm:px-6 md:grid-cols-[1.4fr_1fr_1fr] lg:px-8">
        <div>
          <div className="flex items-center gap-2 font-heading text-lg font-semibold">
            <span className="grid size-7 place-items-center rounded-md bg-primary text-primary-foreground">
              <Database className="size-3.5" aria-hidden />
            </span>
            Mesa de Precios
          </div>
          <p className="mt-3 max-w-md text-[11px] leading-relaxed text-muted-foreground">
            Herramienta local de consulta y auditoría para compras municipales. Sin servicios
            en la nube, sin llaves de acceso y sin identificación de proveedores. Construida
            para el Datatón INE 2026.
          </p>
        </div>
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Fuente de datos
          </p>
          <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground">
            Instituto Nacional de Estadística (INE), Guatemala. Datos publicados en{" "}
            <a
              href="https://datos.ine.gob.gt"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 font-medium text-foreground underline decoration-border underline-offset-2 hover:text-primary"
            >
              datos.ine.gob.gt
              <ExternalLink className="size-2.5" aria-hidden />
            </a>{" "}
            y en el portal institucional. Las licencias y la hora UTC de cada archivo están en
            la sección de trazabilidad.
          </p>
        </div>
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
            Reproducibilidad
          </p>
          <p className="mt-2 text-[11px] leading-relaxed text-muted-foreground">
            Pipeline en Python con <code className="font-mono text-[10px]">uv</code>; aplicación
            Next.js con <code className="font-mono text-[10px]">pnpm</code>. Los comandos y las
            limitaciones están en el README del repositorio. Las cifras se recalculan desde los
            archivos crudos y se validan con pruebas.
          </p>
        </div>
      </div>
      <div className="border-t border-border/60">
        <div className="mx-auto flex max-w-7xl flex-col gap-1 px-4 py-3 text-[10px] text-muted-foreground sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
          <span>INE · Datatón 2026 · Categoría tecnológica y ciencias de datos</span>
          <span>Valores nominales · Sin ajuste por inflación · Uso informativo</span>
        </div>
      </div>
    </footer>
  );
}
