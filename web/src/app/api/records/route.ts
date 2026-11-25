import { NextRequest, NextResponse } from "next/server";

import { loadRecords, loadSummary } from "@/lib/data";
import { queryRecords } from "@/lib/query";
import type { SourceGroup } from "@/lib/types";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const SOURCES: SourceGroup[] = ["DPIR", "IPMC", "ICC", "BASKETS"];

export async function GET(request: NextRequest) {
  const params = request.nextUrl.searchParams;
  const requested = params.get("source") ?? "DPIR";
  const source = (SOURCES.includes(requested as SourceGroup) ? requested : "DPIR") as SourceGroup;

  try {
    const result = queryRecords(loadRecords(), loadSummary(), {
      source,
      q: params.get("q") ?? undefined,
      from: params.get("from") ?? undefined,
      to: params.get("to") ?? undefined,
      metric: params.get("metric") ?? undefined,
      unit: params.get("unit") ?? undefined,
      includeAlerts: params.get("alerts") === "1",
      page: Number(params.get("page") ?? "1") || 1,
      pageSize: Number(params.get("pageSize") ?? "25") || 25,
    });
    return NextResponse.json(result, {
      headers: { "Cache-Control": "no-store" },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Error desconocido";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
