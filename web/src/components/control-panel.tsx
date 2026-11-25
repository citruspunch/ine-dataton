"use client";

import { CalendarDays, RotateCcw } from "lucide-react";

import {
  Card,
  CardContent,
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
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MONTH_NAMES, formatNumber } from "@/lib/format";
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
  onReset: () => void;
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
  onReset,
  meta,
}: ControlPanelProps) {
  return (
    <Card className="lg:sticky lg:top-[5.25rem]">
      <CardContent className="space-y-5 p-5">
        <div>
          <h2 className="text-[15px] font-semibold tracking-tight">Tu cálculo</h2>
          <p className="mt-0.5 text-[12.5px] text-muted-foreground">
            Ajusta tu hogar y el periodo.
          </p>
        </div>

        <section>
          <Label className="text-[13px] font-medium">Área</Label>
          <RadioGroup
            value={area}
            onValueChange={(value) => onAreaChange(value as Area)}
            className="mt-2 grid grid-cols-2 gap-2"
            aria-label="Área de la canasta básica alimentaria"
          >
            {(["Urbana", "Rural"] as const).map((option) => (
              <label
                key={option}
                className="relative flex cursor-pointer flex-col rounded-lg border border-border bg-card px-3 py-2.5 transition-colors hover:bg-muted/60 has-data-[state=checked]:border-primary has-data-[state=checked]:bg-primary has-data-[state=checked]:text-primary-foreground has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-ring has-[:focus-visible]:ring-offset-2 has-[:focus-visible]:ring-offset-background"
              >
                <RadioGroupItem
                  value={option}
                  aria-label={`Canasta ${option.toLowerCase()}`}
                  className="sr-only"
                />
                <span className="text-[13px] font-medium leading-tight">
                  {option}
                </span>
                <span className="mt-0.5 text-[12px] leading-tight opacity-75">
                  {formatNumber(meta.areas[option].referenceKcal)} kcal/día
                </span>
              </label>
            ))}
          </RadioGroup>
        </section>

        <section>
          <div className="flex items-baseline justify-between gap-3">
            <Label htmlFor="members" className="text-[13px] font-medium">
              Integrantes del hogar
            </Label>
            <div className="flex items-baseline gap-1.5">
              <span className="font-mono text-[22px] font-semibold leading-none tabular-nums">
                {members}
              </span>
              <span className="text-[12px] text-muted-foreground">
                {members === 1 ? "persona" : "personas"}
              </span>
            </div>
          </div>
          <Slider
            id="members"
            min={1}
            max={8}
            step={1}
            value={[members]}
            onValueChange={(values) => onMembersChange(values[0] ?? 1)}
            aria-label="Número de integrantes del hogar"
            className="mt-3 [&_[data-slot=slider-thumb]]:size-5 [&_[data-slot=slider-track]]:h-1.5"
          />
          <div className="mt-1 flex justify-between text-[12px] text-muted-foreground">
            <span>1</span>
            <span>8</span>
          </div>
        </section>

        <section>
          <div className="flex items-center justify-between gap-2">
            <Label className="flex items-center gap-1.5 text-[13px] font-medium">
              <CalendarDays className="size-3.5 text-muted-foreground" />
              Periodo
            </Label>
            <span className="text-[11.5px] text-muted-foreground">
              hasta octubre 2026
            </span>
          </div>
          <div className="mt-2 grid grid-cols-[1.3fr_1fr] gap-2">
            <div>
              <Label htmlFor="month" className="sr-only">
                Mes
              </Label>
              <Select
                value={String(month)}
                onValueChange={(value) => onMonthChange(Number(value))}
              >
                <SelectTrigger id="month" className="h-10 w-full text-[13px]">
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
            <div>
              <Label htmlFor="year" className="sr-only">
                Año
              </Label>
              <Select
                value={String(year)}
                onValueChange={(value) => onYearChange(Number(value))}
              >
                <SelectTrigger id="year" className="h-10 w-full text-[13px]">
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
        </section>

        <section>
          <Label className="text-[13px] font-medium">Tipo de costo</Label>
          <Tabs
            value={mode}
            onValueChange={(value) => onModeChange(value as Mode)}
            className="mt-2"
          >
            <TabsList className="grid h-10 w-full grid-cols-2">
              <TabsTrigger value="total" className="text-[12.5px]">
                Costo mensual
              </TabsTrigger>
              <TabsTrigger value="kcal" className="text-[12.5px]">
                Por 1.000 kcal
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </section>

        <section>
          <Label htmlFor="variation" className="text-[13px] font-medium">
            Variación del IPC
          </Label>
          <Select
            value={variation}
            onValueChange={(value) => onVariationChange(value as VariationType)}
          >
            <SelectTrigger
              id="variation"
              className="mt-2 h-10 w-full text-[13px]"
            >
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="monthly">Mensual</SelectItem>
              <SelectItem value="interannual">Interanual (12 meses)</SelectItem>
            </SelectContent>
          </Select>

          <div className="mt-2.5 flex items-start justify-between gap-3 rounded-lg bg-muted/60 px-3 py-2.5">
            <div className="min-w-0">
              <Label htmlFor="direct" className="text-[13px] font-medium">
                Calcular sin empalme
              </Label>
              <p className="mt-0.5 text-[12px] leading-snug text-muted-foreground">
                Muestra por qué no se mezclan bases del IPC.
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

        <div className="border-t border-border/70 pt-4">
          <button
            type="button"
            onClick={onReset}
            className="inline-flex items-center gap-1.5 text-[12.5px] text-muted-foreground transition-colors hover:text-foreground"
          >
            <RotateCcw className="size-3" />
            Restablecer valores
          </button>
        </div>
      </CardContent>
    </Card>
  );
}
