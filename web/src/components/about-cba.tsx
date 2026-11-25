"use client";

import { BookOpen } from "lucide-react";

import { SourcesDialog } from "@/components/sources-dialog";
import { Card, CardContent } from "@/components/ui/card";

export function AboutCba() {
  return (
    <Card className="hidden lg:block">
      <CardContent className="p-5">
        <p className="flex items-center gap-1.5 text-[13px] font-medium">
          <BookOpen className="size-3.5 text-primary" />
          Sobre la CBA
        </p>
        <p className="mt-1.5 text-[12.5px] leading-relaxed text-muted-foreground">
          Es una referencia mínima de alimentos: no mide el gasto real de un
          hogar ni la pobreza.
        </p>
        <SourcesDialog
          trigger={
            <button
              type="button"
              className="mt-2 text-[12.5px] font-medium text-primary underline-offset-2 hover:underline"
            >
              Cómo se calcula
            </button>
          }
        />
      </CardContent>
    </Card>
  );
}
