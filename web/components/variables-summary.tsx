import type { VariablesSummary as Summary } from "@/lib/types";

export function VariablesSummary({ summary }: { summary?: Summary | null }) {
  if (!summary) return null;
  const notes = summary.coverage?.notes;
  return (
    <section className="space-y-3 rounded-xl border border-line bg-white p-5 print:break-inside-avoid">
      <div>
        <h2 className="text-lg font-bold">Resumen de variables y unidades</h2>
        <p className="text-sm text-muted">
          {summary.row_count} filas leídas
          {summary.coverage?.period ? ` · ${summary.coverage.period}` : ""}. Los valores
          excluidos no pudieron convertirse al tipo declarado.
        </p>
      </div>
      {notes ? <p className="text-sm leading-relaxed">{notes}</p> : null}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="border-b border-line bg-[#f2f2f2] text-[12px] text-muted">
            <tr>
              <th className="px-2 py-2 font-bold">Variable / encabezado</th>
              <th className="px-2 py-2 font-bold">Tipo</th>
              <th className="px-2 py-2 font-bold">Unidad</th>
              <th className="px-2 py-2 font-bold">Base o alcance</th>
              <th className="px-2 py-2 text-right font-bold">Válidos</th>
              <th className="px-2 py-2 text-right font-bold">Nulos</th>
              <th className="px-2 py-2 text-right font-bold">Excluidos</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {summary.columns.map((column) => (
              <tr key={column.name}>
                <td className="px-2 py-2 align-top">
                  <span className="font-mono text-[12.5px]">{column.name}</span>
                  <span className="text-muted"> / {column.column}</span>
                  {column.notes ? (
                    <div className="mt-0.5 text-[12px] text-muted">{column.notes}</div>
                  ) : null}
                </td>
                <td className="px-2 py-2 align-top">
                  {column.type}
                  {column.nullable ? " · admite nulos" : ""}
                </td>
                <td className="px-2 py-2 align-top">{column.unit || "No declarada"}</td>
                <td className="px-2 py-2 align-top">
                  {column.reference || "No declarado"}
                </td>
                <td className="px-2 py-2 text-right align-top tabular-nums">
                  {column.valid_count ?? "—"}
                </td>
                <td className="px-2 py-2 text-right align-top tabular-nums">
                  {column.null_count ?? "—"}
                </td>
                <td className="px-2 py-2 text-right align-top tabular-nums">
                  {column.excluded_count ?? "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {summary.columns.some((column) => !column.present) ? (
        <p className="text-sm text-muted">
          — indica una columna ausente; sus conteos no se evaluaron.
        </p>
      ) : null}
    </section>
  );
}
