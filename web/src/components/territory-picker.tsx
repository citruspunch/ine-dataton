"use client";

import { useMemo } from "react";
import { Combobox as ComboboxPrimitive } from "@base-ui/react";
import { Building2, MapPin } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import {
  Combobox,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxInput,
  ComboboxItem,
  ComboboxList,
} from "@/components/ui/combobox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Department, Municipality } from "@/lib/types";

interface TerritoryPickerProps {
  departments: Department[];
  municipalities: Municipality[];
  departmentCode: string;
  municipalityCode: string;
  onDepartmentChange: (code: string) => void;
  onMunicipalityChange: (code: string) => void;
}

export function TerritoryPicker({
  departments,
  municipalities,
  departmentCode,
  municipalityCode,
  onDepartmentChange,
  onMunicipalityChange,
}: TerritoryPickerProps) {
  const departmentItems = useMemo(
    () =>
      Object.fromEntries(
        departments.map((department) => [department.code, department.name]),
      ),
    [departments],
  );

  const options = useMemo(
    () =>
      municipalities
        .filter((item) => item.department_code === departmentCode)
        .sort((a, b) => a.name.localeCompare(b.name, "es")),
    [municipalities, departmentCode],
  );

  const items = useMemo(
    () =>
      ComboboxPrimitive.createItems(options, {
        getValue: (item) => item.code,
        getLabel: (item) => item.name,
      }),
    [options],
  );

  const departmentName =
    departments.find((item) => item.code === departmentCode)?.name ??
    "el departamento";

  return (
    <Card className="border-border/70 shadow-sm">
      <CardContent className="space-y-4">
        <div>
          <h2 className="text-base font-semibold tracking-tight">Territorio</h2>
          <p className="mt-0.5 text-[13px] text-muted-foreground">
            Elige un departamento y un municipio de los 340 del país.
          </p>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="department"
              className="flex items-center gap-1.5 text-xs font-medium text-foreground"
            >
              <Building2 className="size-3.5 text-muted-foreground" />
              Departamento
            </label>
            <Select
              value={departmentCode}
              onValueChange={(value) => {
                if (typeof value === "string") onDepartmentChange(value);
              }}
              items={departmentItems}
            >
              <SelectTrigger
                id="department"
                className="h-11 w-full rounded-lg border-border bg-background px-3 text-sm"
              >
                <SelectValue placeholder="Selecciona un departamento" />
              </SelectTrigger>
              <SelectContent>
                {departments.map((department) => (
                  <SelectItem key={department.code} value={department.code}>
                    {department.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="flex flex-col gap-1.5">
            <label
              htmlFor="municipality"
              className="flex items-center gap-1.5 text-xs font-medium text-foreground"
            >
              <MapPin className="size-3.5 text-muted-foreground" />
              Municipio
            </label>
            <Combobox
              key={departmentCode}
              items={items}
              value={municipalityCode}
              onValueChange={(value) => {
                if (
                  typeof value === "string" &&
                  options.some((item) => item.code === value)
                ) {
                  onMunicipalityChange(value);
                }
              }}
            >
              <ComboboxInput
                id="municipality"
                placeholder={`Busca en ${departmentName}…`}
                className="h-11! w-full! rounded-lg! border-border! bg-background"
                showClear={false}
              />
              <ComboboxContent>
                <ComboboxEmpty>
                  No hay municipios de {departmentName} con ese nombre.
                </ComboboxEmpty>
                <ComboboxList>
                  {(item: Municipality) => (
                    <ComboboxItem key={item.code} value={item.code}>
                      {item.name}
                    </ComboboxItem>
                  )}
                </ComboboxList>
              </ComboboxContent>
            </Combobox>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
