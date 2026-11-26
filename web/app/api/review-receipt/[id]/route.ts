import { ENGINE_URL } from "@/lib/api";

export const dynamic = "force-dynamic";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const { id } = await params;
  const response = await fetch(`${ENGINE_URL}/review/${id}/receipt.json`, {
    cache: "no-store",
  });
  if (!response.ok) {
    return new Response("Recibo no disponible", { status: response.status });
  }
  return new Response(await response.text(), {
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Content-Disposition": `attachment; filename="recibo-privado-${id}.json"`,
    },
  });
}
