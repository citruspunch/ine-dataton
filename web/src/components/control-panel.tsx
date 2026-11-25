"use client";

import { CalendarDays, Gauge, House, Scale } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MONTH_NAMES, formatNumber, formatPeriodShort } from "@/lib/format";
import type { Area, BasketMeta, Mode, VariationType } from "@/lib/types";

type ControlPanelProps = {
  area: Area;
  onAreaChange: (area: Area) => void;
  members: number;
  onMembersChange: (members: number) => void;
  year: number;
  month: number;
  years: number[];
  availableMonths: number[];
  onYearChange: (year: number) => void;
  onMonthChange: (month: number) => void;
  mode: Mode;
  onModeChange: (mode: Mode) => void;
  variation: VariationType;
  onVariationChange: (variation: VariationType) => void;
  direct: boolean;
  onDirectChange: (direct: boolean) => void;
  meta: BasketMeta;
};

export function ControlPanel({
  area,
  onAreaChange,
  members,
  onMembersChange,
  year,
  month,
  years,
  availableMonths,
  onYearChange,
  onMonthChange,
  mode,
  onModeChange,
  variation,
  onVariationChange,
  direct,
  onDirectChange,
  meta,
}: ControlPanelProps) {
  return (
    <Card className="lg:sticky lg:top-[4.6rem]">
      <CardHeader className="border-b border-border/70 pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <Gauge className="size-4 text-primary" />
          Configura tu cálculo
        </CardTitle>
        <p className="text-[11px] leading-relaxed text-muted-foreground">
          Ajusta el hogar, el periodo y la forma de medir el costo.
        </p>
      </CardHeader>

      <CardContent className="space-y-4 pt-1">
        <section className="space-y-2">
          <div className="flex items-center justify-between">
            <Label className="text-xs font-medium">Área de la canasta</Label>
            <Badge variant="outline" className="text-[10px] text-muted-foreground">
              CBA
            </Badge>
          </div>
          <RadioGroup
            value={area}
            onValueChange={(value) => onAreaChange(value as Area)}
            className="grid grid-cols-2 gap-2"
            aria-label="Área de la canasta básica alimentaria"
          >
            {(["Urbana", "Rural"] as const).map((option) => (
              <label
                key={option}
                className="group relative flex cursor-pointer flex-col gap-0.5 rounded-lg border border-border bg-card px-3 py-2.5 transition-colors hover:bg-muted/60 has-data-[state=checked]:border-primary has-data-[state=checked]:bg-primary/[0.06] has-data-[state=checked]:shadow-[inset_0_0_0_1px_var(--primary)]"
              >
                <RadioGroupItem
                  value={option}
                  aria-label={`Canasta ${option.toLowerCase()}`}
                  className="absolute right-2.5 top-2.5"
                />
                <span className="text-[13px] font-medium leading-tight">
                  {option}
                </span>
                <span className="text-[10.5px] leading-tight text-muted-foreground">
                  {formatNumber(meta.areas[option].referenceKcal)} kcal/día
                </span>
              </label>
            ))}
          </RadioGroup>
        </section>

        <section className="space-y-2">
          <div className="flex items-end justify-between">
            <Label htmlFor="members" className="text-xs font-medium">
              Integrantes del hogar
            </Label>
            <span className="font-mono text-xl font-semibold leading-none tracking-tight tabular-nums">
              {members}
            </span>
          </div>
          <Slider
            id="members"
            min={1}
            max={8}
            step={1}
            value={[members]}
            onValueChange={(values) => onMembersChange(values[0] ?? 1)}
            aria-label="Número de integrantes del hogar"
          />
          <div className="flex justify-between px-0.5 font-mono text-[10px] text-muted-foreground">
            {Array.from({ length: 8 }, (_, index) => index + 1).map((value) => (
              <span
                key={value}
                className={
                  value === members
                    ? "font-semibold text-primary"
                    : "text-muted-foreground/70"
                }
              >
                {value}
              </span>
            ))}
          </div>
          <p className="text-[10.5px] leading-relaxed text-muted-foreground">
            Hogares de 1 a 8 integrantes. No se ajusta por economías de escala.
          </p>
        </section>

        <Separator />

        <section className="space-y-2">
          <div className="flex items-center justify-between">
            <Label className="flex items-center gap-1.5 text-xs font-medium">
              <CalendarDays className="size-3.5 text-muted-foreground" />
              Periodo
            </Label>
            <span className="font-mono text-[10px] text-muted-foreground">
              {formatPeriodShort(`${year}-${String(month).padStart(2, "0")}`)}
            </span>
          </div>
          <div className="grid grid-cols-[1.35fr_1fr] gap-2">
            <div className="space-y-1">
              <Label htmlFor="month" className="sr-only">
                Mes
              </Label>
              <Select
                value={String(month)}
                onValueChange={(value) => onMonthChange(Number(value))}
              >
                <SelectTrigger id="month" className="h-9 w-full text-[13px]">
                  <SelectValue placeholder="Mes" />
                </SelectTrigger>
                <SelectContent>
                  {MONTH_NAMES.map((name, index) => {
                    const value = index + 1;
                    return (
                      <SelectItem
                        key={name}
                        value={String(value)}
                        disabled={!availableMonths.includes(value)}
                      >
                        {name}
                      </SelectItem>
                    );
                  })}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label htmlFor="year" className="sr-only">
                Año
              </Label>
              <Select
                value={String(year)}
                onValueChange={(value) => onYearChange(Number(value))}
              >
                <SelectTrigger id="year" className="h-9 w-full text-[13px]">
                  <SelectValue placeholder="Año" />
                </SelectTrigger>
                <SelectContent>
                  {years.map((option) => (
                    <SelectItem key={option} value={String(option)}>
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
          <p className="text-[10.5px] leading-relaxed text-muted-foreground">
            Disponible de {meta.period.firstLabel} a {meta.period.lastLabel}.
            Noviembre y diciembre de 2026 aún no se publican.
          </p>
        </section>

        <Separator />

        <section className="space-y-2">
          <Label className="flex items-center gap-1.5 text-xs font-medium">
            <Scale className="size-3.5 text-muted-foreground" />
            Modo de análisis
          </Label>
          <Tabs value={mode} onValueChange={(value) => onModeChange(value as Mode)}>
            <TabsList className="grid h-9 w-full grid-cols-2">
              <TabsTrigger value="total" className="text-xs">
                Costo total
              </TabsTrigger>
              <TabsTrigger value="kcal" className="text-xs">
                Por 1.000 kcal
              </TabsTrigger>
            </TabsList>
          </Tabs>
          <p className="text-[10.5px] leading-relaxed text-muted-foreground">
            {mode === "total"
              ? "Gasto mensual completo de la canasta para el hogar."
              : "Costo de 1.000 kcal: mide eficiencia calórica y no depende del tamaño del hogar."}
          </p>
        </section>

        <section className="space-y-2">
          <Label htmlFor="variation" className="text-xs font-medium">
            Variación del IPC
          </Label>
          <Select
            value={variation}
            onValueChange={(value) => onVariationChange(value as VariationType)}
          >
            <SelectTrigger id="variation" className="h-9 w-full text-[13px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="monthly">Mensual (mes anterior)</SelectItem>
              <SelectItem value="interannual">Interanual (12 meses)</SelectItem>
            </SelectContent>
          </Select>

          <div className="mt-2 flex items-start justify-between gap-3 rounded-lg border border-dashed border-border bg-muted/40 px-3 py-2.5">
            <div className="min-w-0">
              <Label htmlFor="direct" className="text-[11.5px] font-medium">
                Cálculo directo sin empalme
              </Label>
              <p className="mt-0.5 text-[10.5px] leading-snug text-muted-foreground">
                Modo didáctico: mezcla las bases del IPC para mostrar la
                distorsión.
              </p>
            </div>
            <Switch
              id="direct"
              checked={direct}
              onCheckedChange={onDirectChange}
              aria-label="Calcular la variación sin aplicar el empalme oficial"
            />
          </div>
        </section>
      </CardContent>

      <CardFooter className="justify-between gap-2 py-2.5 text-[10px] leading-snug text-muted-foreground">
        <span className="inline-flex items-center gap-1">
          <House className="size-3" />
          {meta.daysPerMonth} días por mes
        </span>
        <span className="font-mono">INE · {meta.period.count} meses</span>
      </CardFooter>
    </Card>
  );
}
