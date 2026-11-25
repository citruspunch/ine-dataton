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
  Plus,
  Trash,
  WarningCircle,
} from "@phosphor-icons/react/dist/ssr";

import { createProfile, validateProfileYaml } from "@/app/actions";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
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
import { cn } from "@/lib/utils";
import type { ActionState } from "@/lib/types";

type ColumnType = "integer" | "float" | "string" | "date";
type PeriodMode = "expected" | "range";

let uid = 0;
const nextUid = () => ++uid;

interface ColumnDraft {
  uid: number;
  name: string;
  column: string;
  type: ColumnType;
  role: "" | "period_year" | "period_month";
  nullable: boolean;
}

interface SeriesDraft {
  uid: number;
  id: string;
  label: string;
  index: string;
  base: string;
  variation: string;
  comparable: boolean;
  reason: string;
}

interface CheckDraft {
  uid: number;
  id: string;
  label: string;
  numeratorField: string;
  numeratorPeriod: string;
  denominatorField: string;
  denominatorPeriod: string;
  publishedField: string;
  publishedPeriod: string;
  tolerance: string;
  unit: string;
}

const COLUMN_TYPES: { value: ColumnType; label: string }[] = [
  { value: "integer", label: "Entero" },
  { value: "float", label: "Decimal" },
  { value: "string", label: "Texto" },
  { value: "date", label: "Fecha" },
];

function initialColumns(): ColumnDraft[] {
  return [
    {
      uid: nextUid(),
      name: "year",
      column: "Año",
      type: "integer",
      role: "period_year",
      nullable: false,
    },
    {
      uid: nextUid(),
      name: "month",
      column: "Mes",
      type: "string",
      role: "period_month",
      nullable: false,
    },
    {
      uid: nextUid(),
      name: "value",
      column: "Índice",
      type: "float",
      role: "",
      nullable: false,
    },
  ];
}

function initialSeries(): SeriesDraft[] {
  return [
    {
      uid: nextUid(),
      id: "serie",
      label: "Serie principal",
      index: "value",
      base: "2024=100",
      variation: "",
      comparable: true,
      reason: "",
    },
  ];
}

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
  topic: string;
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
  rangeFrom: string;
  rangeTo: string;
  grainExtra: string;
  unit: string;
  series: SeriesDraft[];
  checks: CheckDraft[];
  displayPeriod: string;
  displayBase: string;
  displayUnit: string;
}

function initialDraft(): Draft {
  return {
    profileId: "",
    version: "1.0.0",
    kind: "delimited",
    topic: "",
    title: "",
    description: "",
    expectedSheet: "",
    headerRow: "1",
    columns: initialColumns(),
    dateYear: "year",
    dateMonth: "month",
    monthFormat: "number",
    periodMode: "expected",
    periods: ["2025-01"],
    rangeFrom: "",
    rangeTo: "",
    grainExtra: "",
    unit: "índice",
    series: initialSeries(),
    checks: [],
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
  if (draft.topic.trim()) lines.push(`topic: ${scalar(draft.topic)}`);
  lines.push(`title: ${scalar(draft.title)}`);
  lines.push(`description: ${block(draft.description, 2)}`);
  lines.push(
    `expected_sheet: ${draft.kind === "xlsx" ? scalar(draft.expectedSheet) : "null"}`,
  );
  lines.push(`header_row: ${Number.parseInt(draft.headerRow, 10) || 1}`);

  lines.push("");
  lines.push("schema:");
  for (const column of columns) {
    lines.push(`  - name: ${scalar(column.name)}`);
    lines.push(`    column: ${scalar(column.column)}`);
    lines.push(`    type: ${column.type}`);
    if (column.role) lines.push(`    role: ${column.role}`);
    if (column.nullable) lines.push("    nullable: true");
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
    lines.push(`    from: ${scalar(draft.rangeFrom)}`);
    lines.push(`    to: ${scalar(draft.rangeTo)}`);
  } else {
    lines.push("  expected:");
    for (const period of draft.periods) lines.push(`    - ${scalar(period)}`);
  }

  lines.push("");
  lines.push("comparability:");
  lines.push(`  unit: ${scalar(draft.unit)}`);
  if (draft.series.length) {
    lines.push("  series:");
    for (const series of draft.series) {
      lines.push(`    - id: ${scalar(series.id)}`);
      lines.push(`      label: ${scalar(series.label)}`);
      lines.push(`      index: ${scalar(series.index)}`);
      lines.push(`      base: ${scalar(series.base)}`);
      if (series.variation) lines.push(`      variation: ${scalar(series.variation)}`);
      lines.push(`      comparable: ${series.comparable}`);
      if (!series.comparable && series.reason.trim()) {
        lines.push(`      reason: ${block(series.reason, 8)}`);
      }
    }
  } else {
    lines.push("  series: []");
  }
  if (!draft.checks.length) {
    lines.push("  checks: []");
  } else {
    lines.push("  checks:");
    for (const check of draft.checks) {
      lines.push(`    - id: ${scalar(check.id)}`);
      lines.push(`      label: ${scalar(check.label)}`);
      lines.push("      numerator:");
      lines.push(`        field: ${scalar(check.numeratorField)}`);
      lines.push(`        period: ${scalar(check.numeratorPeriod)}`);
      lines.push("      denominator:");
      lines.push(`        field: ${scalar(check.denominatorField)}`);
      lines.push(`        period: ${scalar(check.denominatorPeriod)}`);
      if (check.publishedField && check.publishedPeriod) {
        lines.push("      published:");
        lines.push(`        field: ${scalar(check.publishedField)}`);
        lines.push(`        period: ${scalar(check.publishedPeriod)}`);
      }
      if (check.tolerance.trim()) {
        lines.push(`      tolerance_pp: ${Number(check.tolerance)}`);
      }
      if (check.unit.trim()) lines.push(`      unit: ${scalar(check.unit)}`);
    }
  }

  const displayPeriod =
    draft.displayPeriod.trim() ||
    (draft.periodMode === "range"
      ? `${draft.rangeFrom} a ${draft.rangeTo}`.trim()
      : draft.periods.join(", "));
  const displayBase = draft.displayBase.trim() || draft.series[0]?.base || "";
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
  if (!draft.columns.some((column) => column.name.trim() && column.column.trim())) {
    problems.push("Declare al menos una columna.");
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
  if (draft.periodMode === "range" && (!draft.rangeFrom || !draft.rangeTo)) {
    problems.push("Complete el rango de periodos.");
  }
  if (!draft.series.some((series) => series.index.trim() && series.base.trim())) {
    problems.push("Declare al menos una serie comparable con índice y base.");
  }
  return problems;
}

export function NewProfileDialog() {
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

  function updateColumn(uidValue: number, patch: Partial<ColumnDraft>) {
    setDraft((current) => ({
      ...current,
      columns: current.columns.map((column) =>
        column.uid === uidValue ? { ...column, ...patch } : column,
      ),
    }));
  }

  function updateSeries(uidValue: number, patch: Partial<SeriesDraft>) {
    setDraft((current) => ({
      ...current,
      series: current.series.map((series) =>
        series.uid === uidValue ? { ...series, ...patch } : series,
      ),
    }));
  }

  function updateCheck(uidValue: number, patch: Partial<CheckDraft>) {
    setDraft((current) => ({
      ...current,
      checks: current.checks.map((check) =>
        check.uid === uidValue ? { ...check, ...patch } : check,
      ),
    }));
  }

  const localProblems = showErrors ? validateDraft(draft) : [];
  const errors = state.errors ?? [];
  const liveValid =
    checked && !checking && liveErrors.length === 0 && Boolean(draft.profileId);

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="secondary" size="sm" type="button" className="whitespace-nowrap">
          <Plus className="h-4 w-4" aria-hidden />
          Nueva regla
        </Button>
      </DialogTrigger>
      <DialogContent className="w-[min(960px,94vw)] p-0">
        <div className="border-b border-line px-6 py-4">
          <DialogHeader className="mb-0">
            <DialogTitle>Nuevo perfil declarativo</DialogTitle>
            <DialogDescription>
              El formulario construye el contrato. La validación revisa campos, grano,
              periodos y comparabilidad antes de guardar el archivo en <code>profiles/</code>.
            </DialogDescription>
          </DialogHeader>
        </div>

        <form
          action={formAction}
          onSubmit={(event) => {
            setShowErrors(true);
            if (validateDraft(draft).length) event.preventDefault();
          }}
        >
          <input type="hidden" name="yaml" value={yaml} />
          <div className="max-h-[64vh] space-y-6 overflow-y-auto px-6 py-5">
            <Section number="01" title="Identidad del contrato">
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Identificador" required hint="minúsculas, dígitos y guion bajo">
                  <Input
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
                <Field label="Versión" required>
                  <Input
                    value={draft.version}
                    onChange={(event) => update("version", event.target.value)}
                    placeholder="1.0.0"
                  />
                </Field>
                <Field label="Título" required>
                  <Input
                    value={draft.title}
                    onChange={(event) => update("title", event.target.value)}
                    placeholder="IPC mensual, República"
                  />
                </Field>
                <Field label="Tema" hint="Opcional. Agrupa perfiles por tema, por ejemplo ipc.">
                  <Input
                    value={draft.topic}
                    onChange={(event) => update("topic", event.target.value)}
                    placeholder="ipc"
                  />
                </Field>
                <div className="sm:col-span-2">
                  <Field label="Descripción">
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
                <Field label="Tipo de archivo" required>
                  <DraftSelect
                    value={draft.kind}
                    onChange={(value) => update("kind", value as Draft["kind"])}
                    options={[
                      { value: "delimited", label: "CSV / delimitado" },
                      { value: "xlsx", label: "Libro de Excel" },
                    ]}
                  />
                </Field>
                <Field label="Fila de encabezados" required>
                  <Input
                    type="number"
                    min={1}
                    value={draft.headerRow}
                    onChange={(event) => update("headerRow", event.target.value)}
                  />
                </Field>
                {draft.kind === "xlsx" ? (
                  <Field label="Hoja esperada" required>
                    <Input
                      value={draft.expectedSheet}
                      onChange={(event) => update("expectedSheet", event.target.value)}
                      placeholder="Hoja1"
                    />
                  </Field>
                ) : null}
              </div>
            </Section>

            <Section
              number="03"
              title="Columnas"
              description="Cada columna se resuelve por su encabezado, nunca por coordenadas fijas."
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
                        role: "",
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
              <div className="space-y-3">
                <div className="hidden grid-cols-[1.1fr_1.2fr_0.9fr_1fr_auto] gap-2 px-1 text-[11px] font-bold uppercase tracking-[0.08em] text-muted sm:grid">
                  <span>Campo interno</span>
                  <span>Encabezado</span>
                  <span>Tipo</span>
                  <span>Rol</span>
                  <span />
                </div>
                {draft.columns.map((column) => (
                  <div
                    key={column.uid}
                    className="grid gap-2 rounded-lg border border-line bg-[#fafafa] p-3 sm:grid-cols-[1.1fr_1.2fr_0.9fr_1fr_auto] sm:items-center sm:border-0 sm:bg-transparent sm:p-0"
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
                    <DraftSelect
                      value={column.role || "none"}
                      onChange={(value) =>
                        updateColumn(column.uid, {
                          role: value === "none" ? "" : (value as ColumnDraft["role"]),
                        })
                      }
                      options={[
                        { value: "none", label: "Dato" },
                        { value: "period_year", label: "Año" },
                        { value: "period_month", label: "Mes" },
                      ]}
                      ariaLabel="Rol"
                    />
                    <div className="flex items-center justify-between gap-2 sm:justify-end">
                      <label className="flex items-center gap-1.5 text-[12px] text-muted">
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
                        onClick={() =>
                          update(
                            "columns",
                            draft.columns.filter((item) => item.uid !== column.uid),
                          )
                        }
                        aria-label="Quitar columna"
                      >
                        <Trash className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </Section>

            <Section number="04" title="Periodo y grano">
              <div className="grid gap-4 sm:grid-cols-3">
                <Field label="Campo de año" required>
                  <DraftSelect
                    value={draft.dateYear}
                    onChange={(value) => update("dateYear", value)}
                    options={fieldOptions}
                    placeholder="Seleccione"
                  />
                </Field>
                <Field label="Campo de mes" required>
                  <DraftSelect
                    value={draft.dateMonth}
                    onChange={(value) => update("dateMonth", value)}
                    options={fieldOptions}
                    placeholder="Seleccione"
                  />
                </Field>
                <Field label="Formato del mes" required>
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
                <Field label="Campo adicional del grano" hint="Opcional. Por ejemplo, un indicador.">
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
                <Field label="Periodos declarados" required>
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
                <div className="mt-3 grid gap-4 sm:grid-cols-2">
                  <Field label="Desde" required>
                    <Input
                      value={draft.rangeFrom}
                      onChange={(event) => update("rangeFrom", event.target.value)}
                      placeholder="2025-01"
                    />
                  </Field>
                  <Field label="Hasta" required>
                    <Input
                      value={draft.rangeTo}
                      onChange={(event) => update("rangeTo", event.target.value)}
                      placeholder="2025-12"
                    />
                  </Field>
                </div>
              ) : (
                <div className="mt-3">
                  <PeriodsInput
                    periods={draft.periods}
                    onChange={(periods) => update("periods", periods)}
                  />
                </div>
              )}
            </Section>

            <Section number="05" title="Comparabilidad">
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Unidad" required>
                  <Input
                    value={draft.unit}
                    onChange={(event) => update("unit", event.target.value)}
                    placeholder="índice"
                  />
                </Field>
                <div className="flex items-end pb-2 text-[12px] text-muted">
                  Una serie solo es comparable si declara su base.
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between">
                <p className="text-[12px] font-bold uppercase tracking-[0.1em] text-muted">
                  Series
                </p>
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() =>
                    update("series", [
                      ...draft.series,
                      {
                        uid: nextUid(),
                        id: `serie_${draft.series.length + 1}`,
                        label: "",
                        index: "",
                        base: "",
                        variation: "",
                        comparable: true,
                        reason: "",
                      },
                    ])
                  }
                >
                  <Plus className="h-3.5 w-3.5" aria-hidden />
                  Serie
                </Button>
              </div>
              <div className="mt-3 space-y-3">
                {draft.series.map((series, index) => (
                  <div
                    key={series.uid}
                    className="space-y-3 rounded-lg border border-line bg-[#fafafa] p-4"
                  >
                    <div className="flex items-center justify-between">
                      <p className="text-[12px] font-semibold text-muted">Serie {index + 1}</p>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted hover:text-fail"
                        onClick={() =>
                          update(
                            "series",
                            draft.series.filter((item) => item.uid !== series.uid),
                          )
                        }
                        aria-label="Quitar serie"
                      >
                        <Trash className="h-4 w-4" />
                      </Button>
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <Field label="Identificador">
                        <Input
                          value={series.id}
                          onChange={(event) => updateSeries(series.uid, { id: event.target.value })}
                          placeholder="serie_f"
                        />
                      </Field>
                      <Field label="Etiqueta">
                        <Input
                          value={series.label}
                          onChange={(event) =>
                            updateSeries(series.uid, { label: event.target.value })
                          }
                          placeholder="Serie F · base 2024=100"
                        />
                      </Field>
                      <Field label="Campo índice" required>
                        <DraftSelect
                          value={series.index}
                          onChange={(value) => updateSeries(series.uid, { index: value })}
                          options={fieldOptions}
                          placeholder="Seleccione"
                        />
                      </Field>
                      <Field label="Base" required>
                        <Input
                          value={series.base}
                          onChange={(event) =>
                            updateSeries(series.uid, { base: event.target.value })
                          }
                          placeholder="2024=100"
                        />
                      </Field>
                      <Field label="Campo de variación publicada" hint="opcional">
                        <DraftSelect
                          value={series.variation || "none"}
                          onChange={(value) =>
                            updateSeries(series.uid, {
                              variation: value === "none" ? "" : value,
                            })
                          }
                          options={[{ value: "none", label: "Ninguno" }, ...fieldOptions]}
                        />
                      </Field>
                      <div className="flex items-center gap-2 pt-6">
                        <Checkbox
                          checked={series.comparable}
                          onChange={(event) =>
                            updateSeries(series.uid, { comparable: event.target.checked })
                          }
                        />
                        <span className="text-[13px] text-ink">
                          Comparable con las demás series
                        </span>
                      </div>
                    </div>
                    {!series.comparable ? (
                      <Field label="Motivo de no comparabilidad">
                        <Textarea
                          className="min-h-[64px]"
                          value={series.reason}
                          onChange={(event) =>
                            updateSeries(series.uid, { reason: event.target.value })
                          }
                          placeholder="Base distinta: el cociente no es una variación."
                        />
                      </Field>
                    ) : null}
                  </div>
                ))}
              </div>

              <div className="mt-6 flex items-center justify-between">
                <div>
                  <p className="text-[12px] font-bold uppercase tracking-[0.1em] text-muted">
                    Comparaciones
                  </p>
                  <p className="text-[12px] text-muted">
                    Opcional. Cada comprobación contrasta dos periodos de la misma base.
                  </p>
                </div>
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={() =>
                    update("checks", [
                      ...draft.checks,
                      {
                        uid: nextUid(),
                        id: `comparacion_${draft.checks.length + 1}`,
                        label: "",
                        numeratorField: draft.series[0]?.index ?? "",
                        numeratorPeriod: "",
                        denominatorField: draft.series[0]?.index ?? "",
                        denominatorPeriod: "",
                        publishedField: "",
                        publishedPeriod: "",
                        tolerance: "0.005",
                        unit: "porcentaje",
                      },
                    ])
                  }
                >
                  <Plus className="h-3.5 w-3.5" aria-hidden />
                  Comparación
                </Button>
              </div>
              <div className="mt-3 space-y-3">
                {draft.checks.map((check, index) => (
                  <div
                    key={check.uid}
                    className="space-y-3 rounded-lg border border-line bg-[#fafafa] p-4"
                  >
                    <div className="flex items-center justify-between">
                      <p className="text-[12px] font-semibold text-muted">
                        Comparación {index + 1}
                      </p>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-muted hover:text-fail"
                        onClick={() =>
                          update(
                            "checks",
                            draft.checks.filter((item) => item.uid !== check.uid),
                          )
                        }
                        aria-label="Quitar comparación"
                      >
                        <Trash className="h-4 w-4" />
                      </Button>
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <Field label="Identificador">
                        <Input
                          value={check.id}
                          onChange={(event) => updateCheck(check.uid, { id: event.target.value })}
                        />
                      </Field>
                      <Field label="Etiqueta">
                        <Input
                          value={check.label}
                          onChange={(event) =>
                            updateCheck(check.uid, { label: event.target.value })
                          }
                          placeholder="Variación mensual de enero"
                        />
                      </Field>
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2">
                      <Field label="Campo del numerador">
                        <DraftSelect
                          value={check.numeratorField}
                          onChange={(value) =>
                            updateCheck(check.uid, { numeratorField: value })
                          }
                          options={fieldOptions}
                          placeholder="Seleccione"
                        />
                      </Field>
                      <Field label="Periodo del numerador">
                        <Input
                          value={check.numeratorPeriod}
                          onChange={(event) =>
                            updateCheck(check.uid, { numeratorPeriod: event.target.value })
                          }
                          placeholder="2025-01"
                        />
                      </Field>
                      <Field label="Campo del denominador">
                        <DraftSelect
                          value={check.denominatorField}
                          onChange={(value) =>
                            updateCheck(check.uid, { denominatorField: value })
                          }
                          options={fieldOptions}
                          placeholder="Seleccione"
                        />
                      </Field>
                      <Field label="Periodo del denominador">
                        <Input
                          value={check.denominatorPeriod}
                          onChange={(event) =>
                            updateCheck(check.uid, { denominatorPeriod: event.target.value })
                          }
                          placeholder="2024-12"
                        />
                      </Field>
                      <Field label="Campo de variación publicada" hint="opcional">
                        <DraftSelect
                          value={check.publishedField || "none"}
                          onChange={(value) =>
                            updateCheck(check.uid, {
                              publishedField: value === "none" ? "" : value,
                            })
                          }
                          options={[{ value: "none", label: "Sin variación publicada" }, ...fieldOptions]}
                        />
                      </Field>
                      <Field label="Periodo de la variación publicada" hint="opcional">
                        <Input
                          value={check.publishedPeriod}
                          onChange={(event) =>
                            updateCheck(check.uid, { publishedPeriod: event.target.value })
                          }
                          placeholder="2025-01"
                        />
                      </Field>
                      <Field label="Tolerancia en puntos porcentuales">
                        <Input
                          value={check.tolerance}
                          onChange={(event) =>
                            updateCheck(check.uid, { tolerance: event.target.value })
                          }
                          placeholder="0.005"
                        />
                      </Field>
                      <Field label="Unidad de la comparación">
                        <Input
                          value={check.unit}
                          onChange={(event) => updateCheck(check.uid, { unit: event.target.value })}
                          placeholder="porcentaje"
                        />
                      </Field>
                    </div>
                  </div>
                ))}
              </div>
            </Section>

            <Section
              number="06"
              title="Presentación pública"
              description="Texto que verá quien consulta el agregado. Si queda vacío, el formulario usa lo declarado arriba."
            >
              <div className="grid gap-4 sm:grid-cols-3">
                <Field label="Periodo mostrado">
                  <Input
                    value={draft.displayPeriod}
                    onChange={(event) => update("displayPeriod", event.target.value)}
                    placeholder="diciembre 2024 y enero 2025"
                  />
                </Field>
                <Field label="Base mostrada">
                  <Input
                    value={draft.displayBase}
                    onChange={(event) => update("displayBase", event.target.value)}
                    placeholder="2024=100"
                  />
                </Field>
                <Field label="Unidad mostrada">
                  <Input
                    value={draft.displayUnit}
                    onChange={(event) => update("displayUnit", event.target.value)}
                    placeholder="índice"
                  />
                </Field>
              </div>
            </Section>

            <details className="rounded-lg border border-line bg-[#fafafa] px-4 py-3">
              <summary className="flex cursor-pointer list-none items-center gap-2 text-[13px] font-semibold text-brand">
                <BracketsCurly className="h-4 w-4" aria-hidden />
                Vista previa del YAML generado
              </summary>
              <pre className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap break-words rounded-md bg-[#1a1a1a] p-3 font-mono text-[11.5px] leading-relaxed text-[#f0f0f0]">
                {yaml}
              </pre>
            </details>
          </div>

          <div className="space-y-3 border-t border-line bg-[#fafafa] px-6 py-4">
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
                  "flex items-center gap-1.5 text-[12.5px]",
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
              <label className="flex items-center gap-2 text-[13px] text-muted">
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
          <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-soft text-[11px] font-bold text-brand">
            {number}
          </span>
          <div>
            <h3 className="text-[14px] font-semibold text-ink">{title}</h3>
            {description ? (
              <p className="mt-0.5 text-[12px] text-muted">{description}</p>
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
  children,
}: {
  label: string;
  required?: boolean;
  hint?: string;
  children: React.ReactNode;
}) {
  const id = useId();
  const control = isValidElement(children)
    ? cloneElement(children as React.ReactElement<{ id?: string }>, { id })
    : children;
  return (
    <div>
      <Label htmlFor={id} className="flex items-center gap-1">
        {label}
        {required ? <span className="text-fail">*</span> : null}
      </Label>
      {control}
      {hint ? <FieldHint>{hint}</FieldHint> : null}
    </div>
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

function PeriodsInput({
  periods,
  onChange,
}: {
  periods: string[];
  onChange: (periods: string[]) => void;
}) {
  const [text, setText] = useState("");
  const valid = /^\d{4}-(0[1-9]|1[0-2])$/.test(text);

  function add() {
    if (!valid || periods.includes(text)) return;
    onChange([...periods, text].sort());
    setText("");
  }

  return (
    <div>
      <Label>Periodos esperados</Label>
      <div className="flex gap-2">
        <Input
          value={text}
          onChange={(event) => setText(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              add();
            }
          }}
          placeholder="2025-01"
          className="max-w-[180px]"
        />
        <Button type="button" variant="secondary" onClick={add} disabled={!valid}>
          <CopySimple className="h-4 w-4" aria-hidden />
          Añadir
        </Button>
      </div>
      {periods.length ? (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {periods.map((period) => (
            <span
              key={period}
              className="inline-flex items-center gap-1 rounded-full border border-line bg-white py-0.5 pl-2.5 pr-1 font-mono text-[11.5px] text-ink"
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
      ) : (
        <FieldHint>Sin periodos, la validación no podrá verificar la cobertura temporal.</FieldHint>
      )}
    </div>
  );
}

function AlertList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-md border border-[#ffb699] bg-fail-bg px-3 py-2 text-[12.5px] text-fail">
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
