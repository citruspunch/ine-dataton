"use client";

import {
  cloneElement,
  isValidElement,
  useActionState,
  useEffect,
  useId,
  useMemo,
  useState,
  useTransition,
} from "react";
import { useRouter } from "next/navigation";
import {
  BracketsCurly,
  CheckCircle,
  CircleNotch,
  CopySimple,
  Info,
  Plus,
  Trash,
  WarningCircle,
} from "@phosphor-icons/react/dist/ssr";

import { createProfile, validateProfileYaml } from "@/app/actions";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Checkbox, FieldHint, Input, Label, Textarea } from "@/components/ui/field";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import type { ActionState } from "@/lib/types";

type ColumnType = "integer" | "float" | "string" | "date";
type PeriodMode = "expected" | "range";

const YEAR_OPTIONS = Array.from({ length: 61 }, (_, index) => {
  const year = String(1990 + index);
  return { value: year, label: year };
});

const MONTH_OPTIONS = Array.from({ length: 12 }, (_, index) => {
  const value = String(index + 1).padStart(2, "0");
  const label = new Intl.DateTimeFormat("es", { month: "long" }).format(
    new Date(2025, index, 1),
  );
  return { value, label: label.charAt(0).toUpperCase() + label.slice(1) };
});

function rangePeriod(year: string, month: string) {
  return year && month ? `${year}-${month}` : "";
}

let uid = 0;
const nextUid = () => {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  uid += 1;
  return `uid-${Date.now()}-${uid}`;
};

interface ColumnDraft {
  uid: string;
  name: string;
  column: string;
  type: ColumnType;
  nullable: boolean;
}

const COLUMN_TYPES: { value: ColumnType; label: string }[] = [
  { value: "integer", label: "Entero" },
  { value: "float", label: "Decimal" },
  { value: "string", label: "Texto" },
  { value: "date", label: "Fecha" },
];

function plainScalar(text: string) {
  return (
    /^[A-Za-z0-9_][A-Za-z0-9 _./=+-]*$/.test(text) &&
    !/^(true|false|null|yes|no|on|off|~)$/i.test(text)
  );
}

function scalar(value: string | number | null) {
  if (value === null) return "null";
  if (typeof value === "number") return String(value);
  const text = value.trim();
  if (!text) return '""';
  return plainScalar(text) ? text : JSON.stringify(text);
}

function block(value: string, indent = 2) {
  const text = value.trim();
  if (!text) return '""';
  const pad = " ".repeat(indent);
  const lines = text.split(/\r?\n/);
  return `|-\n${lines.map((line) => `${pad}${line}`.trimEnd()).join("\n")}`;
}

function uniqueTypes(columns: ColumnDraft[]) {
  const order: ColumnType[] = ["integer", "float", "string", "date"];
  return order.filter((type) => columns.some((column) => column.type === type));
}

interface Draft {
  profileId: string;
  version: string;
  kind: "delimited" | "xlsx";
  title: string;
  description: string;
  expectedSheet: string;
  headerRow: string;
  columns: ColumnDraft[];
  dateYear: string;
  dateMonth: string;
  monthFormat: "number" | "name_es";
  periodMode: PeriodMode;
  periods: string[];
  rangeFromYear: string;
  rangeFromMonth: string;
  rangeToYear: string;
  rangeToMonth: string;
  grainExtra: string;
  unit: string;
  indexField: string;
  base: string;
  displayPeriod: string;
  displayBase: string;
  displayUnit: string;
}

function initialDraft(): Draft {
  return {
    profileId: "",
    version: "1.0.0",
    kind: "delimited",
    title: "",
    description: "",
    expectedSheet: "",
    headerRow: "1",
    columns: [],
    dateYear: "",
    dateMonth: "",
    monthFormat: "number",
    periodMode: "expected",
    periods: ["2025-01"],
    rangeFromYear: "",
    rangeFromMonth: "",
    rangeToYear: "",
    rangeToMonth: "",
    grainExtra: "",
    unit: "índice",
    indexField: "",
    base: "",
    displayPeriod: "",
    displayBase: "",
    displayUnit: "",
  };
}

function buildYaml(draft: Draft): string {
  const columns = draft.columns.filter((column) => column.name.trim() && column.column.trim());
  const grain = [draft.dateYear, draft.dateMonth, draft.grainExtra].filter(Boolean);
  const lines: string[] = [];

  lines.push(`profile_id: ${scalar(draft.profileId)}`);
  lines.push(`version: ${scalar(draft.version || "1.0.0")}`);
  lines.push(`kind: ${draft.kind}`);
  lines.push(`title: ${scalar(draft.title)}`);
  lines.push(`description: ${block(draft.description, 2)}`);
  lines.push(
    `expected_sheet: ${draft.kind === "xlsx" ? scalar(draft.expectedSheet) : "null"}`,
  );
  lines.push(`header_row: ${Number.parseInt(draft.headerRow, 10) || 1}`);

  lines.push("");
  if (columns.length) {
    lines.push("schema:");
    for (const column of columns) {
      lines.push(`  - name: ${scalar(column.name)}`);
      lines.push(`    column: ${scalar(column.column)}`);
      lines.push(`    type: ${column.type}`);
      if (column.nullable) lines.push("    nullable: true");
    }
  } else {
    lines.push("schema: []");
  }

  lines.push("");
  lines.push(`types: [${uniqueTypes(columns).join(", ")}]`);
  lines.push(`grain: [${grain.join(", ")}]`);

  lines.push("");
  lines.push("dates:");
  lines.push(`  year: ${scalar(draft.dateYear)}`);
  lines.push(`  month: ${scalar(draft.dateMonth)}`);
  lines.push(`  month_format: ${draft.monthFormat}`);
  if (draft.periodMode === "range") {
    lines.push("  range:");
    lines.push(
      `    from: ${scalar(rangePeriod(draft.rangeFromYear, draft.rangeFromMonth))}`,
    );
    lines.push(
      `    to: ${scalar(rangePeriod(draft.rangeToYear, draft.rangeToMonth))}`,
    );
  } else {
    lines.push("  expected:");
    for (const period of draft.periods) lines.push(`    - ${scalar(period)}`);
  }

  lines.push("");
  lines.push("comparability:");
  lines.push(`  unit: ${scalar(draft.unit)}`);
  if (draft.indexField) {
    const column = columns.find((entry) => entry.name === draft.indexField);
    lines.push("  series:");
    lines.push("    - id: serie");
    lines.push(`      label: ${scalar(column?.column || draft.indexField)}`);
    lines.push(`      index: ${scalar(draft.indexField)}`);
    lines.push(`      base: ${scalar(draft.base)}`);
    lines.push("      comparable: true");
  } else {
    lines.push("  series: []");
  }
  lines.push("  checks: []");

  const displayPeriod =
    draft.displayPeriod.trim() ||
    (draft.periodMode === "range"
      ? [
          rangePeriod(draft.rangeFromYear, draft.rangeFromMonth),
          rangePeriod(draft.rangeToYear, draft.rangeToMonth),
        ]
          .filter(Boolean)
          .join(" a ")
      : draft.periods.join(", "));
  const displayBase = draft.displayBase.trim() || draft.base;
  const displayUnit = draft.displayUnit.trim() || draft.unit;
  if (displayPeriod || displayBase || displayUnit) {
    lines.push("");
    lines.push("display:");
    if (displayPeriod) lines.push(`  period: ${scalar(displayPeriod)}`);
    if (displayBase) lines.push(`  base: ${scalar(displayBase)}`);
    if (displayUnit) lines.push(`  unit: ${scalar(displayUnit)}`);
  }

  return `${lines.join("\n")}\n`;
}

function validateDraft(draft: Draft): string[] {
  const problems: string[] = [];
  if (!/^[a-z0-9_]+$/.test(draft.profileId)) {
    problems.push("El identificador del perfil solo admite minúsculas, dígitos y guion bajo.");
  }
  if (!draft.title.trim()) problems.push("El título es obligatorio.");
  if (draft.columns.length === 0) {
    problems.push("Agregue al menos una columna antes de guardar el perfil.");
  } else if (draft.columns.some((column) => !column.name.trim() || !column.column.trim())) {
    problems.push("Complete el campo interno y el encabezado de cada columna.");
  }
  if (draft.kind === "xlsx" && !draft.expectedSheet.trim()) {
    problems.push("Un perfil XLSX necesita el nombre de la hoja esperada.");
  }
  if (!draft.dateYear || !draft.dateMonth) {
    problems.push("Seleccione los campos de año y mes.");
  }
  if (draft.periodMode === "expected" && draft.periods.length === 0) {
    problems.push("Declare al menos un periodo esperado.");
  }
  if (draft.periodMode === "range") {
    const from = rangePeriod(draft.rangeFromYear, draft.rangeFromMonth);
    const to = rangePeriod(draft.rangeToYear, draft.rangeToMonth);
    if (!from || !to) {
      problems.push("Complete el inicio y el fin del rango continuo.");
    } else if (to < from) {
      problems.push("El fin del rango no puede ser anterior al inicio.");
    }
  }
  if (!draft.unit.trim()) {
    problems.push("La unidad es obligatoria.");
  }
  if (!draft.base.trim()) {
    problems.push("La base es obligatoria.");
  }
  if (!draft.indexField) {
    problems.push("Seleccione la columna del índice.");
  }
  return problems;
}

export function NewProfileDialog({
  title = "Crear perfil de validación",
}: {
  title?: string;
}) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<Draft>(initialDraft);
  const [showErrors, setShowErrors] = useState(false);
  const [checked, setChecked] = useState(false);
  const [liveErrors, setLiveErrors] = useState<{ field: string; message: string }[]>([]);
  const [checking, startChecking] = useTransition();
  const [state, formAction, pending] = useActionState<ActionState, FormData>(createProfile, {
    ok: true,
  });
  const router = useRouter();

  const yaml = useMemo(() => buildYaml(draft), [draft]);
  const fieldOptions = draft.columns
    .filter((column) => column.name.trim())
    .map((column) => ({ value: column.name, label: `${column.column || column.name} · ${column.name}` }));

  useEffect(() => {
    if (!open) return;
    if (!draft.profileId || !draft.title) return;
    setChecked(false);
    const timer = setTimeout(() => {
      startChecking(async () => {
        const result = await validateProfileYaml(yaml);
        setLiveErrors(result.errors);
        setChecked(true);
      });
    }, 800);
    return () => clearTimeout(timer);
  }, [open, yaml, draft.profileId, draft.title]);

  useEffect(() => {
    if (state.ok && state.profileId) {
      setOpen(false);
      router.refresh();
    }
  }, [state, router]);

  function update<K extends keyof Draft>(key: K, value: Draft[K]) {
    setDraft((current) => ({ ...current, [key]: value }));
  }

  function updateColumn(uidValue: string, patch: Partial<ColumnDraft>) {
    setDraft((current) => ({
      ...current,
      columns: current.columns.map((column) =>
        column.uid === uidValue ? { ...column, ...patch } : column,
      ),
    }));
  }

  function removeColumn(uidValue: string) {
    setDraft((current) => {
      const target = current.columns.find((column) => column.uid === uidValue);
      if (!target) return current;
      const name = target.name;
      return {
        ...current,
        columns: current.columns.filter((column) => column.uid !== uidValue),
        dateYear: current.dateYear === name ? "" : current.dateYear,
        dateMonth: current.dateMonth === name ? "" : current.dateMonth,
        grainExtra: current.grainExtra === name ? "" : current.grainExtra,
        indexField: current.indexField === name ? "" : current.indexField,
      };
    });
  }

  const localProblems = showErrors ? validateDraft(draft) : [];
  const errors = state.errors ?? [];
  const liveValid =
    checked && !checking && liveErrors.length === 0 && Boolean(draft.profileId);

  return (
    <TooltipProvider delayDuration={150}>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogTrigger asChild>
          <Button variant="secondary" size="sm" type="button" className="whitespace-nowrap">
            <Plus className="h-4 w-4" aria-hidden />
            Nueva regla
          </Button>
        </DialogTrigger>
        <DialogContent
          aria-describedby={undefined}
          className="flex w-[min(960px,94vw)] max-h-[88vh] flex-col overflow-hidden p-0"
          onOpenAutoFocus={(event) => {
            event.preventDefault();
            window.setTimeout(() => {
              document.querySelector<HTMLInputElement>("[data-autofocus]")?.focus();
            }, 0);
          }}
        >
          <div className="shrink-0 border-b border-line px-6 py-4">
            <DialogHeader className="mb-0">
              <DialogTitle>{title}</DialogTitle>
            </DialogHeader>
          </div>

          <form
            action={formAction}
            onSubmit={(event) => {
              setShowErrors(true);
              if (validateDraft(draft).length) event.preventDefault();
            }}
            className="flex min-h-0 flex-1 flex-col"
          >
            <input type="hidden" name="yaml" value={yaml} />
            <div className="min-h-0 flex-1 space-y-6 overflow-y-auto px-6 py-5">
              <Section number="01" title="Identidad del contrato">
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field
                    label="Identificador"
                    required
                    hint="minúsculas, dígitos y guion bajo"
                    tooltip="Clave única del perfil en minúsculas, números y guion bajo. Identifica el contrato en profiles/ y vincula los recibos de validación a esta definición."
                  >
                    <Input
                      data-autofocus
                      value={draft.profileId}
                      onChange={(event) =>
                        update(
                          "profileId",
                          event.target.value.toLowerCase().replace(/[^a-z0-9_]/g, "_"),
                        )
                      }
                      placeholder="ipc_mensual_v1"
                    />
                  </Field>
                  <Field
                    label="Versión"
                    required
                    tooltip="Versión del contrato (por ejemplo, 1.0.0). Forma parte del digest de validación, por lo que cambiarla invalida aprobaciones anteriores si cambia el perfil."
                  >
                    <Input
                      value={draft.version}
                      onChange={(event) => update("version", event.target.value)}
                      placeholder="1.0.0"
                    />
                  </Field>
                  <div className="sm:col-span-2">
                    <Field
                      label="Título"
                      required
                      tooltip="Nombre legible del perfil para mostrar en la bandeja de revisión, la ficha y la consulta pública."
                    >
                      <Input
                        value={draft.title}
                        onChange={(event) => update("title", event.target.value)}
                        placeholder="IPC mensual, República"
                      />
                    </Field>
                  </div>
                  <div className="sm:col-span-2">
                    <Field
                      label="Descripción"
                      tooltip="Contexto breve para el revisor sobre el conjunto o agregado que cubre el contrato, su alcance y los supuestos clave declarados."
                    >
                      <Textarea
                        value={draft.description}
                        onChange={(event) => update("description", event.target.value)}
                        placeholder="Qué archivo valida este contrato y qué supuestos declara."
                      />
                    </Field>
                  </div>
                </div>
              </Section>

              <Section number="02" title="Estructura del archivo">
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field
                    label="Tipo de archivo"
                    required
                    tooltip="Formato del archivo a validar. Elige entre archivo delimitado (CSV) o libro de Excel (XLSX/XLS)."
                  >
                    <DraftSelect
                      value={draft.kind}
                      onChange={(value) => {
                        const kind = value as Draft["kind"];
                        setDraft((current) => ({
                          ...current,
                          kind,
                          expectedSheet: kind === "xlsx" ? current.expectedSheet : "",
                        }));
                      }}
                      options={[
                        { value: "delimited", label: "CSV / delimitado" },
                        { value: "xlsx", label: "Libro de Excel" },
                      ]}
                    />
                  </Field>
                  <Field
                    label="Fila de encabezados"
                    required
                    tooltip="Número de fila (empezando en 1) donde están los nombres de las columnas. Útil cuando el archivo tiene títulos o celdas combinadas antes de la tabla."
                  >
                    <Input
                      type="number"
                      min={1}
                      placeholder="1"
                      value={draft.headerRow}
                      onChange={(event) => update("headerRow", event.target.value)}
                    />
                  </Field>
                  {draft.kind === "xlsx" ? (
                    <Field
                      label="Hoja esperada"
                      required
                      tooltip="Nombre exacto de la única pestaña del libro de Excel que debe leerse (por ejemplo, Hoja2). Si no existe, la validación falla y muestra las hojas encontradas."
                    >
                      <Input
                        value={draft.expectedSheet}
                        onChange={(event) => update("expectedSheet", event.target.value)}
                        placeholder="Hoja1"
                        autoComplete="off"
                        spellCheck={false}
                      />
                    </Field>
                  ) : null}
                </div>
              </Section>

              <Section
                number="03"
                title="Columnas"
                action={
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={() =>
                      update("columns", [
                        ...draft.columns,
                        {
                          uid: nextUid(),
                          name: "",
                          column: "",
                          type: "float",
                          nullable: false,
                        },
                      ])
                    }
                  >
                    <Plus className="h-3.5 w-3.5" aria-hidden />
                    Columna
                  </Button>
                }
              >
                {draft.columns.length ? (
                  <div className="space-y-3">
                    <div className="hidden grid-cols-[1.1fr_1.2fr_0.9fr_auto] gap-2 px-1 text-[12px] font-bold text-muted sm:grid">
                      <span className="flex items-center gap-1">
                        Campo interno
                        <InfoTip
                          label="Campo interno"
                          text="Nombre interno que usan las reglas y el contrato para referirse a esta columna, sin depender del texto exacto del encabezado."
                        />
                      </span>
                      <span className="flex items-center gap-1">
                        Encabezado
                        <InfoTip
                          label="Encabezado"
                          text="Texto exacto del encabezado de columna en el archivo de datos. El lector resuelve la columna por nombre de encabezado."
                        />
                      </span>
                      <span className="flex items-center gap-1">
                        Tipo
                        <InfoTip
                          label="Tipo"
                          text="Tipo de dato esperado para validar que los valores de la columna se puedan convertir sin error."
                        />
                      </span>
                      <span />
                    </div>
                    {draft.columns.map((column) => (
                      <div
                        key={column.uid}
                        className="grid gap-2 rounded-lg border border-line bg-[#fafafa] p-3 sm:grid-cols-[1.1fr_1.2fr_0.9fr_auto] sm:items-center sm:border-0 sm:bg-transparent sm:p-0"
                      >
                        <Input
                          value={column.name}
                          onChange={(event) =>
                            updateColumn(column.uid, {
                              name: event.target.value.toLowerCase().replace(/[^a-z0-9_]/g, "_"),
                            })
                          }
                          placeholder="year"
                          aria-label="Campo interno"
                        />
                        <Input
                          value={column.column}
                          onChange={(event) => updateColumn(column.uid, { column: event.target.value })}
                          placeholder="Año"
                          aria-label="Encabezado"
                        />
                        <DraftSelect
                          value={column.type}
                          onChange={(value) => updateColumn(column.uid, { type: value as ColumnType })}
                          options={COLUMN_TYPES}
                          ariaLabel="Tipo"
                        />
                        <div className="flex items-center justify-between gap-2 sm:justify-end">
                          <label className="flex items-center gap-1.5 text-[13px] text-muted">
                            <Checkbox
                              checked={column.nullable}
                              onChange={(event) =>
                                updateColumn(column.uid, { nullable: event.target.checked })
                              }
                            />
                            Nulo
                          </label>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className="h-8 w-8 text-muted hover:text-fail"
                            onClick={() => removeColumn(column.uid)}
                            aria-label="Quitar columna"
                          >
                            <Trash className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="rounded-lg border border-dashed border-[#c7c7c7] bg-[#fafafa] px-4 py-8 text-center">
                    <p className="text-[14px] text-muted">
                      No hay columnas definidas todavía. Usa + Columna para agregar una.
                    </p>
                  </div>
                )}
              </Section>

              <Section number="04" title="Periodo y grano">
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field
                    label="Campo de año"
                    required
                    tooltip="Columna que aporta el año de cada registro para validar fechas y periodos."
                  >
                    <DraftSelect
                      value={draft.dateYear}
                      onChange={(value) => update("dateYear", value)}
                      options={fieldOptions}
                      placeholder="Seleccione"
                    />
                  </Field>
                  <Field
                    label="Campo de mes"
                    required
                    tooltip="Columna que aporta el mes de cada registro para validar fechas y periodos."
                  >
                    <DraftSelect
                      value={draft.dateMonth}
                      onChange={(value) => update("dateMonth", value)}
                      options={fieldOptions}
                      placeholder="Seleccione"
                    />
                  </Field>
                  <Field
                    label="Formato del mes"
                    required
                    tooltip="Formato en que vienen los meses en el archivo (números del 1 al 12 o nombres en español) para parsearlos sin errores ni orden alfabético."
                  >
                    <DraftSelect
                      value={draft.monthFormat}
                      onChange={(value) =>
                        update("monthFormat", value as Draft["monthFormat"])
                      }
                      options={[
                        { value: "number", label: "Número del 1 al 12" },
                        { value: "name_es", label: "Nombre en español" },
                      ]}
                    />
                  </Field>
                  <Field
                    label="Campo adicional del grano"
                    tooltip="Columna extra (por ejemplo, indicador o territorio) que junto con el periodo define qué hace única a una fila y detecta grano duplicado."
                  >
                    <DraftSelect
                      value={draft.grainExtra || "none"}
                      onChange={(value) => update("grainExtra", value === "none" ? "" : value)}
                      options={[
                        { value: "none", label: "Ninguno" },
                        ...fieldOptions.filter(
                          (option) =>
                            option.value !== draft.dateYear && option.value !== draft.dateMonth,
                        ),
                      ]}
                    />
                  </Field>
                </div>
              </Section>

              <Section number="05" title="Rango de periodos">
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field
                    label="Periodos declarados"
                    required
                    tooltip="Define si el contrato espera una lista puntual de periodos o un rango continuo entre un inicio y un fin."
                  >
                    <DraftSelect
                      value={draft.periodMode}
                      onChange={(value) => update("periodMode", value as PeriodMode)}
                      options={[
                        { value: "expected", label: "Lista de periodos" },
                        { value: "range", label: "Rango continuo" },
                      ]}
                    />
                  </Field>
                </div>

                {draft.periodMode === "range" ? (
                  <div className="mt-4 space-y-3">
                    <div className="flex items-center gap-1.5">
                      <p className="text-[14px] font-semibold text-ink">Límites del rango</p>
                      <InfoTip
                        label="Límites del rango"
                        text="Inicio y fin del rango continuo esperado (año y mes) para comprobar que las fechas del archivo caigan dentro del periodo declarado."
                      />
                    </div>
                    <div className="grid gap-4 sm:grid-cols-2">
                      <RangeBound
                        label="Desde"
                        year={draft.rangeFromYear}
                        month={draft.rangeFromMonth}
                        onYear={(value) => update("rangeFromYear", value)}
                        onMonth={(value) => update("rangeFromMonth", value)}
                      />
                      <RangeBound
                        label="Hasta"
                        year={draft.rangeToYear}
                        month={draft.rangeToMonth}
                        onYear={(value) => update("rangeToYear", value)}
                        onMonth={(value) => update("rangeToMonth", value)}
                      />
                    </div>
                  </div>
                ) : (
                  <div className="mt-3">
                    <PeriodsInput
                      periods={draft.periods}
                      onChange={(periods) => update("periods", periods)}
                      tooltip="Lista explícita de periodos válidos (por ejemplo, 2025-01) que el archivo debe cubrir sin mezclar periodos fuera de lo declarado."
                    />
                  </div>
                )}
              </Section>

              <Section number="06" title="Comparabilidad">
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field
                    label="Unidad"
                    required
                    tooltip="Unidad de medida declarada para los valores del conjunto (por ejemplo, índice o porcentaje)."
                  >
                    <Input
                      value={draft.unit}
                      onChange={(event) => update("unit", event.target.value)}
                      placeholder="índice"
                    />
                  </Field>
                  <Field
                    label="Base"
                    required
                    tooltip="Periodo o año base de referencia del indicador. Permite distinguir cambios metodológicos de base antes de comparar series."
                  >
                    <Input
                      value={draft.base}
                      onChange={(event) => update("base", event.target.value)}
                      placeholder="2024=100"
                    />
                  </Field>
                  <Field
                    label="Columna del índice"
                    required
                    tooltip="Columna que contiene los valores del indicador que se publican y comparan."
                  >
                    <DraftSelect
                      value={draft.indexField}
                      onChange={(value) => update("indexField", value)}
                      options={fieldOptions}
                      placeholder="Seleccione"
                    />
                  </Field>
                </div>
              </Section>

              <Section number="07" title="Presentación pública">
                <div className="grid gap-4 sm:grid-cols-3">
                  <Field
                    label="Periodo mostrado"
                    tooltip="Texto opcional para mostrar el periodo en la consulta pública. Si queda vacío, se usa el periodo declarado en el contrato."
                  >
                    <Input
                      value={draft.displayPeriod}
                      onChange={(event) => update("displayPeriod", event.target.value)}
                      placeholder="diciembre 2024 y enero 2025"
                    />
                  </Field>
                  <Field
                    label="Base mostrada"
                    tooltip="Etiqueta opcional de base de referencia para la vista pública. Si queda vacía, se toma la base declarada en el perfil."
                  >
                    <Input
                      value={draft.displayBase}
                      onChange={(event) => update("displayBase", event.target.value)}
                      placeholder="2024=100"
                    />
                  </Field>
                  <Field
                    label="Unidad mostrada"
                    tooltip="Etiqueta opcional de unidad para la consulta pública. Si queda vacía, se usa la unidad declarada en el perfil."
                  >
                    <Input
                      value={draft.displayUnit}
                      onChange={(event) => update("displayUnit", event.target.value)}
                      placeholder="índice"
                    />
                  </Field>
                </div>
              </Section>

              <div className="rounded-lg border border-line bg-[#fafafa] px-4 py-3">
                <p className="flex items-center gap-2 text-[14px] font-semibold text-brand">
                  <BracketsCurly className="h-4 w-4" aria-hidden />
                  Vista previa del YAML generado
                </p>
                <pre className="mt-3 overflow-x-auto whitespace-pre-wrap break-words rounded-md bg-[#1a1a1a] p-3 font-mono text-[12.5px] leading-relaxed text-[#f0f0f0]">
                  {yaml}
                </pre>
              </div>
            </div>

            <div className="shrink-0 space-y-3 border-t border-line bg-[#fafafa] px-6 py-4">
              {localProblems.length ? (
                <AlertList title="Revise el formulario" items={localProblems} />
              ) : null}
              {errors.length ? (
                <AlertList
                  title="La validación encontró errores"
                  items={errors.map((error) => `${error.field}: ${error.message}`)}
                />
              ) : null}
              {!localProblems.length && !errors.length && draft.profileId && draft.title ? (
                <p
                  className={cn(
                    "flex items-center gap-1.5 text-[13.5px]",
                    liveValid ? "text-ok" : "text-muted",
                  )}
                >
                  {checking ? (
                    <>
                      <CircleNotch className="h-3.5 w-3.5 animate-spin" aria-hidden />
                      Validando el contrato…
                    </>
                  ) : liveValid ? (
                    <>
                      <CheckCircle className="h-3.5 w-3.5" aria-hidden />
                      El contrato es válido. Puede guardarlo.
                    </>
                  ) : (
                    <>
                      <WarningCircle className="h-3.5 w-3.5" aria-hidden />
                      {liveErrors.length} error(es) de validación.
                    </>
                  )}
                </p>
              ) : null}

              <div className="flex flex-wrap items-center justify-between gap-3">
                <label className="flex items-center gap-2 text-[14px] text-muted">
                  <Checkbox name="overwrite" />
                  Sobrescribir si el identificador ya existe
                </label>
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => {
                      setDraft(initialDraft());
                      setShowErrors(false);
                      setLiveErrors([]);
                    }}
                  >
                    Limpiar
                  </Button>
                  <Button type="submit" disabled={pending}>
                    {pending ? (
                      <>
                        <CircleNotch className="h-4 w-4 animate-spin" aria-hidden />
                        Guardando…
                      </>
                    ) : (
                      "Guardar perfil"
                    )}
                  </Button>
                </div>
              </div>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </TooltipProvider>
  );
}

function Section({
  number,
  title,
  description,
  action,
  children,
}: {
  number: string;
  title: string;
  description?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-soft text-[12px] font-bold text-brand">
            {number}
          </span>
          <div>
            <h3 className="text-[15px] font-semibold text-ink">{title}</h3>
            {description ? (
              <p className="mt-0.5 text-[13px] text-muted">{description}</p>
            ) : null}
          </div>
        </div>
        {action}
      </div>
      <div className="rounded-lg border border-line p-4">{children}</div>
    </section>
  );
}

function Field({
  label,
  required,
  hint,
  tooltip,
  children,
}: {
  label: string;
  required?: boolean;
  hint?: string;
  tooltip?: string;
  children: React.ReactNode;
}) {
  const id = useId();
  const control = isValidElement(children)
    ? cloneElement(children as React.ReactElement<{ id?: string }>, { id })
    : children;
  return (
    <div>
      <div className="mb-1.5 flex items-center gap-1.5">
        <Label htmlFor={id} className="mb-0 flex items-center gap-1">
          {label}
          {required ? <span className="text-fail">*</span> : null}
        </Label>
        {tooltip ? <InfoTip label={label} text={tooltip} /> : null}
      </div>
      {control}
      {hint ? <FieldHint>{hint}</FieldHint> : null}
    </div>
  );
}

function InfoTip({ label, text }: { label: string; text: string }) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <button
          type="button"
          aria-label={`Más información sobre ${label}`}
          className="inline-flex h-4 w-4 items-center justify-center rounded-full text-muted transition-colors hover:text-brand focus-visible:text-brand"
        >
          <Info className="h-3.5 w-3.5" aria-hidden />
        </button>
      </TooltipTrigger>
      <TooltipContent>{text}</TooltipContent>
    </Tooltip>
  );
}

function DraftSelect({
  id,
  value,
  onChange,
  options,
  placeholder,
  ariaLabel,
}: {
  id?: string;
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
  placeholder?: string;
  ariaLabel?: string;
}) {
  const selected = options.find((option) => option.value === value);
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger id={id} aria-label={ariaLabel} className="h-10">
        <SelectValue placeholder={placeholder ?? "Seleccione"}>{selected?.label}</SelectValue>
      </SelectTrigger>
      <SelectContent>
        {options.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

function RangeBound({
  label,
  year,
  month,
  onYear,
  onMonth,
}: {
  label: string;
  year: string;
  month: string;
  onYear: (value: string) => void;
  onMonth: (value: string) => void;
}) {
  return (
    <div>
      <p className="mb-1.5 text-[14px] font-semibold text-ink">{label}</p>
      <div className="grid grid-cols-2 gap-2">
        <DraftSelect
          value={year}
          onChange={onYear}
          options={YEAR_OPTIONS}
          placeholder="Año"
          ariaLabel={`${label}: año`}
        />
        <DraftSelect
          value={month}
          onChange={onMonth}
          options={MONTH_OPTIONS}
          placeholder="Mes"
          ariaLabel={`${label}: mes`}
        />
      </div>
    </div>
  );
}

function PeriodsInput({
  periods,
  onChange,
  tooltip,
}: {
  periods: string[];
  onChange: (periods: string[]) => void;
  tooltip?: string;
}) {
  const [year, setYear] = useState("");
  const [month, setMonth] = useState("");
  const value = rangePeriod(year, month);
  const canAdd = Boolean(value) && !periods.includes(value);

  function add() {
    if (!canAdd) return;
    onChange([...periods, value].sort());
    setYear("");
    setMonth("");
  }

  return (
    <div>
      <div className="mb-1.5 flex items-center gap-1.5">
        <Label className="mb-0">Periodos esperados</Label>
        {tooltip ? <InfoTip label="Periodos esperados" text={tooltip} /> : null}
      </div>
      <div className="grid gap-2 sm:grid-cols-[160px_190px_max-content] sm:items-center">
        <DraftSelect
          value={year}
          onChange={setYear}
          options={YEAR_OPTIONS}
          placeholder="Año"
          ariaLabel="Año del periodo"
        />
        <DraftSelect
          value={month}
          onChange={setMonth}
          options={MONTH_OPTIONS}
          placeholder="Mes"
          ariaLabel="Mes del periodo"
        />
        <Button type="button" variant="secondary" onClick={add} disabled={!canAdd}>
          <CopySimple className="h-4 w-4" aria-hidden />
          Añadir
        </Button>
      </div>
      {periods.length ? (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {periods.map((period) => (
            <span
              key={period}
              className="inline-flex items-center gap-1 rounded-full border border-line bg-white py-0.5 pl-2.5 pr-1 font-mono text-[12.5px] text-ink"
            >
              {period}
              <button
                type="button"
                onClick={() => onChange(periods.filter((item) => item !== period))}
                className="rounded-full p-0.5 text-muted hover:bg-fail-bg hover:text-fail"
                aria-label={`Quitar ${period}`}
              >
                <Trash className="h-3 w-3" />
              </button>
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function AlertList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-md border border-[#ffb699] bg-fail-bg px-3 py-2 text-[13.5px] text-fail">
      <p className="flex items-center gap-1.5 font-semibold">
        <WarningCircle className="h-3.5 w-3.5" aria-hidden />
        {title}
      </p>
      <ul className="mt-1 list-disc space-y-0.5 pl-5">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}
