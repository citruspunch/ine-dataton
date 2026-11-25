"use client";

import { ExternalLink, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatDateUtc, formatNumber, formatUtc } from "@/lib/format";
import type { Meta } from "@/lib/types";

export function MethodologySheet({
  open,
  onOpenChange,
  meta,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  meta: Meta;
}) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full gap-0 p-0 sm:max-w-3xl">
        <SheetHeader className="border-b bg-muted/30 px-6 py-5">
          <div className="flex items-center gap-2">
            <div className="flex size-8 items-center justify-center rounded-full bg-primary/10">
              <ShieldCheck className="size-4 text-primary" />
            </div>
            <div>
              <SheetTitle className="font-display text-xl">
                Metodología, fuentes y privacidad
              </SheetTitle>
              <SheetDescription>
                Cómo se construyen las tasas, qué se suprime y de dónde vienen los datos.
              </SheetDescription>
            </div>
          </div>
        </SheetHeader>

        <ScrollArea className="h-[calc(100vh-110px)]">
          <div className="space-y-8 px-6 py-6 text-sm leading-relaxed">
            <section className="space-y-3">
              <h3 className="font-display text-lg font-semibold">Cómo leer el radar</h3>
              <p className="text-muted-foreground">
                Cada vista declara el <strong className="text-foreground">criterio territorial</strong>{" "}
                activo. <strong className="text-foreground">Residencia</strong> asigna el evento al
                municipio donde vive la persona; <strong className="text-foreground">ocurrencia</strong>{" "}
                lo asigna al municipio donde sucedió. Son definiciones distintas y nunca se suman
                entre sí.
              </p>
              <p className="text-muted-foreground">
                La tasa se calcula como <span className="font-mono text-xs">casos ÷ población
                proyectada 2025 × 10,000</span>. El denominador es siempre la proyección municipal
                del INE (ambos sexos). El Censo 2018 se muestra solo como referencia y{" "}
                <strong className="text-foreground">nunca</strong> se usa para calcular tasas.
              </p>
              <div className="grid gap-2 sm:grid-cols-3">
                <InfoTile label="Año de eventos" value="2025" />
                <InfoTile label="Denominador" value="Proyección 2025" />
                <InfoTile label="Base de tasa" value="10,000 hab." />
              </div>
            </section>

            <section className="space-y-3">
              <h3 className="font-display text-lg font-semibold">Secreto estadístico</h3>
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline">General: &lt; 5 se suprime</Badge>
                <Badge variant="outline">Homicidio/suicidio: &lt; 10</Badge>
                <Badge variant="outline">Sin municipio × día</Badge>
                <Badge variant="outline">Sin marca/color/modelo</Badge>
              </div>
              <p className="text-muted-foreground">
                {meta.suppression.text} {meta.suppression.smallCellPolicy}
              </p>
              <p className="rounded-xl border border-amber-200 bg-amber-50/70 p-3 text-sm text-amber-950">
                <strong>Qué significa una celda rayada:</strong> existe, pero su conteo es menor al
                umbral. No se publica el número ni la tasa porque, con la población conocida, la tasa
                permitiría reconstruir el conteo. La aplicación muestra “—” y una alerta, nunca un
                valor numérico.
              </p>
            </section>

            <section className="space-y-3">
              <h3 className="font-display text-lg font-semibold">Capa de puntos</h3>
              <p className="text-muted-foreground">
                Los puntos son los centroides de los {formatNumber(meta.pointLayer.source_places)}{" "}
                lugares poblados del Censo 2018, no la ubicación de cada evento. Se excluyen{" "}
                {formatNumber(meta.pointLayer.excluded_suffix_999)} códigos terminados en{" "}
                <span className="font-mono">999</span> (“otros lugares poblados”) y{" "}
                {formatNumber(meta.pointLayer.excluded_missing_coordinates)} registros sin
                coordenadas; ambos grupos se superponen. Quedan{" "}
                {formatNumber(meta.pointLayer.included)} puntos visibles.
              </p>
            </section>

            <section className="space-y-3">
              <h3 className="font-display text-lg font-semibold">Fuentes oficiales y trazabilidad</h3>
              <p className="text-muted-foreground">
                El pipeline revisa primero los archivos locales. Si falta uno, lo descarga del banco
                de datos del INE y registra URL, fecha UTC y SHA-256. Generado:{" "}
                <span className="font-mono text-xs">{formatUtc(meta.generatedAtUtc)}</span>.
              </p>
              <div className="overflow-hidden rounded-xl border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-xs font-medium">Archivo</TableHead>
                      <TableHead className="text-xs font-medium">Fecha UTC</TableHead>
                      <TableHead className="text-xs font-medium">SHA-256</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {meta.provenance.map((row) => (
                      <TableRow key={row.filename} className="align-top text-sm">
                        <TableCell className="max-w-[220px] whitespace-normal py-2">
                          <a
                            href={row.url}
                            target="_blank"
                            rel="noreferrer"
                            className="flex items-start gap-1 font-medium text-primary hover:underline"
                          >
                            <span className="min-w-0 break-words">{row.filename}</span>
                            <ExternalLink className="mt-0.5 size-3 shrink-0" />
                          </a>
                          <p className="mt-0.5 text-xs text-muted-foreground">
                            {row.publisher}
                          </p>
                        </TableCell>
                        <TableCell className="whitespace-nowrap py-2 text-xs text-muted-foreground">
                          {formatDateUtc(row.retrieved_at_utc)}
                          <br />
                          {row.origin === "download" ? "descargado" : "caché local"}
                        </TableCell>
                        <TableCell className="py-2">
                          <code
                            className="block max-w-[180px] truncate text-xs text-muted-foreground"
                            title={row.sha256}
                          >
                            {row.sha256.slice(0, 16)}…
                          </code>
                          <span className="text-sm text-muted-foreground">
                            {formatNumber(row.bytes / 1024)} KB
                          </span>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
              <p className="text-sm text-muted-foreground">
                Los límites administrativos provienen de geoBoundaries / OCHA FISS (CC BY 3.0 IGO).
                Los datos estadísticos son del Instituto Nacional de Estadística de Guatemala.
              </p>
            </section>

            <section className="space-y-3">
              <h3 className="font-display text-lg font-semibold">Límites de esta versión</h3>
              <ul className="space-y-2 text-muted-foreground">
                {meta.limits.map((limit) => (
                  <li key={limit} className="flex gap-2 text-sm leading-relaxed">
                    <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary/60" />
                    {limit}
                  </li>
                ))}
              </ul>
              <p className="rounded-xl bg-muted/50 p-3 text-sm text-muted-foreground">
                <strong className="text-foreground">Horizonte de población:</strong>{" "}
                {meta.population.projectionNote} El análisis usa {meta.populationYear} como año de
                denominador.
              </p>
            </section>

            <section className="space-y-3">
              <h3 className="font-display text-lg font-semibold">Licencias y transparencia</h3>
              <ul className="space-y-2">
                {meta.licenses.map((license) => (
                  <li key={license.name} className="text-sm text-muted-foreground">
                    <strong className="text-foreground">{license.name}:</strong> {license.detail}{" "}
                    {license.url ? (
                      <a
                        href={license.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-primary hover:underline"
                      >
                        {license.url}
                      </a>
                    ) : null}
                  </li>
                ))}
              </ul>
              <p className="rounded-xl border border-border/80 bg-card p-3 text-sm leading-relaxed text-muted-foreground">
                <strong className="text-foreground">Uso de IA:</strong> {meta.aiDisclosure}
              </p>
            </section>
          </div>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}

function InfoTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border/70 bg-muted/30 p-3">
      <p className="text-xs font-medium text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 text-sm font-semibold">{value}</p>
    </div>
  );
}
