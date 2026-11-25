import { BookOpen, CircleAlert, Compass, Layers, Scale } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DictionaryEntry } from "@/lib/types";

const methodCards = [
  {
    icon: Scale,
    title: "Precios de referencia (DPIR)",
    text: "Dos instantáneas congeladas: junio 2022 y agosto 2023. No son una serie mensual continua. El archivo 2023 contiene la mayor parte del 2022, por lo que los registros repetidos se marcan como duplicados y se excluyen de la banda.",
  },
  {
    icon: Compass,
    title: "Índices, no precios",
    text: "El IPMC mide 89 materiales con base diciembre 2018 = 100; el ICC mide el costo de una vivienda social básica con base 2025 = 100. Un valor de 105 no significa Q105: significa 5% sobre la referencia.",
  },
  {
    icon: Layers,
    title: "Canastas, no cotizaciones",
    text: "La CBAU y la CBAR reportan el costo por persona y por producto. El precio por producto es implícito y corresponde a la cantidad base (por ejemplo, 454 gramos). La ventana disponible es 2024–2026.",
  },
  {
    icon: CircleAlert,
    title: "Corte y calidad",
    text: "El corte se lee de la última fecha con dato válido. Las comas de miles se convierten; las fechas imposibles, los duplicados y los valores faltantes se marcan y no entran en los resúmenes.",
  },
];

export function Methodology({ dictionary }: { dictionary: DictionaryEntry[] }) {
  return (
    <section id="metodologia" className="border-t border-border/60 bg-card/40">
      <div className="mx-auto max-w-7xl px-4 py-14 sm:px-6 lg:px-8">
        <div className="max-w-3xl">
          <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
            Metodología
          </p>
          <h2 className="mt-2 font-heading text-3xl font-semibold tracking-tight sm:text-4xl">
            Qué se puede concluir y qué no.
          </h2>
          <p className="mt-3 text-pretty text-sm leading-relaxed text-muted-foreground sm:text-base">
            La herramienta está diseñada para lectura pre-cotización. Ayuda a ver una banda y
            a detectar problemas de calidad; no reemplaza el análisis de mercado, la
            verificación de especificaciones ni la normativa de contratación pública.
          </p>
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-2">
          {methodCards.map((card) => (
            <Card key={card.title} className="border-border/80 bg-card/80">
              <CardHeader className="gap-2 pb-2">
                <span className="grid size-8 place-items-center rounded-lg bg-primary/10 text-primary">
                  <card.icon className="size-4" aria-hidden />
                </span>
                <CardTitle className="font-heading text-lg">{card.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-[12px] leading-relaxed text-muted-foreground">{card.text}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="mt-4 grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
          <Card className="border-border/80 bg-card/80">
            <CardHeader className="pb-2">
              <CardTitle className="font-heading text-lg">Cómo se calcula la banda</CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-[12px] leading-relaxed text-muted-foreground">
                <li>
                  <strong className="font-medium text-foreground">Mediana y cuartiles:</strong>{" "}
                  sobre los valores numéricos válidos del filtro, con interpolación lineal entre
                  observaciones ordenadas.
                </li>
                <li>
                  <strong className="font-medium text-foreground">Duplicados:</strong> se conserva
                  la copia con NOG completo y, en empate, la del archivo 2023; las demás se
                  excluyen de los cálculos.
                </li>
                <li>
                  <strong className="font-medium text-foreground">Fechas inválidas:</strong> se
                  muestran con su texto original, pero no entran en la mediana ni en el corte.
                </li>
                <li>
                  <strong className="font-medium text-foreground">Presentaciones:</strong> un saco
                  no es una libra. Cuando hay varias presentaciones, la aplicación lo advierte y
                  permite acotar la comparación.
                </li>
                <li>
                  <strong className="font-medium text-foreground">Valores nominales:</strong> no se
                  ajustan por inflación ni por tipo de cambio; son los valores publicados por el INE.
                </li>
              </ul>
            </CardContent>
          </Card>

          <Card className="border-border/80 bg-card/80">
            <CardHeader className="pb-2">
              <CardTitle className="flex items-center gap-2 font-heading text-lg">
                <BookOpen className="size-4 text-primary" aria-hidden />
                Límites explícitos
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-[12px] leading-relaxed text-muted-foreground">
                <li>El DPIR no es una serie mensual: son cortes congelados y discontinuos.</li>
                <li>El ICC solo cubre 2026 y la Región I; el IPMC cubre la Región I Metropolitana.</li>
                <li>Las canastas cubren 2024–2026 y no son precios de mercado independientes.</li>
                <li>
                  No se identifican proveedores, postores ni empresas; los campos de entidad
                  requirente del DPIR se omiten.
                </li>
                <li>
                  Los datos no sustituyen una cotización formal ni una revisión jurídica de las
                  bases de licitación.
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>

        {dictionary.length > 0 ? (
          <details className="group mt-4 rounded-xl border border-border/80 bg-card/70 p-4 open:bg-card/90">
            <summary className="cursor-pointer list-none text-sm font-medium">
              <span className="inline-flex items-center gap-2">
                <BookOpen className="size-4 text-primary" aria-hidden />
                Diccionario de variables del DPIR
                <span className="text-[10px] font-normal text-muted-foreground">
                  ({dictionary.length} definiciones)
                </span>
              </span>
            </summary>
            <div className="mt-3 grid gap-x-6 gap-y-2 border-t border-border/60 pt-3 md:grid-cols-2">
              {dictionary.map((entry) => (
                <div key={entry.variable} className="text-[11px] leading-relaxed">
                  <span className="font-mono font-medium text-foreground">{entry.variable}</span>
                  <span className="text-muted-foreground"> — {entry.description}</span>
                </div>
              ))}
            </div>
          </details>
        ) : null}
      </div>
    </section>
  );
}
