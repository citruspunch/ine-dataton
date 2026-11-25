import { BookOpen } from "lucide-react";

import type { DictionaryEntry, Manifest } from "@/lib/types";

export function MethodNotes({
  dictionary,
  manifest,
}: {
  dictionary: DictionaryEntry[];
  manifest: Manifest;
}) {
  return (
    <section className="border-t border-border/60 py-12">
      <div className="max-w-2xl">
        <h2 className="font-heading text-2xl font-semibold tracking-tight">Cómo leer los datos</h2>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          La herramienta ayuda a leer una banda y detectar problemas de calidad. No sustituye
          una cotización, una revisión de especificaciones ni la normativa de contratación.
        </p>
      </div>

      <div className="mt-8 grid gap-8 md:grid-cols-3">
        <div>
          <h3 className="text-base font-medium">Precios, índices y canastas</h3>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            El DPIR son precios observados en compras públicas. El IPMC y el ICC son índices:
            un valor de 105 significa 5% sobre la referencia, no Q105. Las canastas reportan
            costo por persona; el precio por producto es implícito y corresponde a la cantidad
            base.
          </p>
        </div>
        <div>
          <h3 className="text-base font-medium">Duplicados y alertas</h3>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            El archivo 2023 contiene casi todo el 2022. Se conserva la copia con NOG completo y,
            en empate, la más reciente. Las fechas inválidas, los duplicados y los valores
            faltantes se excluyen de los resúmenes y se pueden revisar con “Mostrar alertas”.
          </p>
        </div>
        <div>
          <h3 className="text-base font-medium">Límites</h3>
          <ul className="mt-2 space-y-1.5 text-sm leading-relaxed text-muted-foreground">
            <li>El DPIR no es una serie mensual continua.</li>
            <li>IPMC e ICC cubren la Región I; el ICC solo 2026.</li>
            <li>Las canastas cubren 2024–2026.</li>
            <li>Valores nominales, sin ajuste por inflación.</li>
            <li>No se identifican proveedores ni postores.</li>
          </ul>
        </div>
      </div>

      <div className="mt-10 grid gap-8 md:grid-cols-2">
        <div>
          <h3 className="text-base font-medium">Cómo se calcula la banda</h3>
          <ul className="mt-2 space-y-1.5 text-sm leading-relaxed text-muted-foreground">
            <li>Se usan solo valores numéricos con fecha válida y sin duplicado.</li>
            <li>Se calculan mínimo, P25, mediana, P75 y máximo con interpolación lineal.</li>
            <li>La mediana no se ve afectada por precios con comas mal formateados.</li>
            <li>El corte del filtro es la última fecha válida de los registros mostrados.</li>
          </ul>
        </div>
        <div>
          <h3 className="text-base font-medium">Atribución y privacidad</h3>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{manifest.attribution}</p>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{manifest.privacy}</p>
        </div>
      </div>

      {dictionary.length > 0 ? (
        <details className="mt-10 rounded-lg border border-border/70 bg-card/60 p-4">
          <summary className="cursor-pointer list-none text-sm font-medium">
            <span className="inline-flex items-center gap-2">
              <BookOpen className="size-4 text-primary" aria-hidden />
              Diccionario de variables del DPIR
              <span className="text-xs font-normal text-muted-foreground">
                ({dictionary.length})
              </span>
            </span>
          </summary>
          <div className="mt-4 grid gap-x-8 gap-y-3 border-t border-border/60 pt-4 md:grid-cols-2">
            {dictionary.map((entry) => (
              <div key={entry.variable} className="text-sm leading-relaxed">
                <span className="font-mono font-medium">{entry.variable}</span>
                <span className="text-muted-foreground"> — {entry.description}</span>
              </div>
            ))}
          </div>
        </details>
      ) : null}

      <p className="mt-8 border-t border-border/60 pt-4 text-xs leading-relaxed text-muted-foreground">
        {manifest.aiDisclosure}
      </p>
    </section>
  );
}
