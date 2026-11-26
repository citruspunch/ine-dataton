"use client";

import { Printer } from "@phosphor-icons/react/dist/ssr";

import { Button } from "@/components/ui/button";

export function PrintButton() {
  return (
    <Button type="button" onClick={() => window.print()} className="print:hidden">
      <Printer className="h-4 w-4" /> Imprimir o guardar en PDF
    </Button>
  );
}
