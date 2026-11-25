"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { errorDetail, postForm, postJson } from "@/lib/api";
import type { ActionState } from "@/lib/types";

function flash(path: string, message: string, kind: "ok" | "warn" | "err" = "ok") {
  redirect(`${path}?msg=${encodeURIComponent(message)}&kind=${kind}`);
}

export async function uploadCase(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const file = formData.get("file");
  if (!(file instanceof File) || file.size === 0) {
    return { ok: false, message: "Seleccione un archivo .csv, .xlsx o .xls." };
  }
  const payload = new FormData();
  payload.append("file", file);
  payload.append("profile", String(formData.get("profile") || ""));
  payload.append("license", String(formData.get("license") || "cc-by"));

  let caseId: string;
  try {
    const result = await postForm<{ case_id: string }>("/review/upload", payload);
    caseId = result.case_id;
  } catch (error) {
    return { ok: false, ...errorDetail(error) };
  }
  revalidatePath("/review");
  redirect(`/review/${caseId}`);
}

export async function submitGate(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const caseId = String(formData.get("case_id") || "");
  const justifications: Record<string, { owner: string; reason: string; policy?: string }> = {};
  for (const key of formData.keys()) {
    if (!key.startsWith("just_owner__")) continue;
    const ruleId = key.slice("just_owner__".length);
    justifications[ruleId] = {
      owner: String(formData.get(`just_owner__${ruleId}`) || ""),
      reason: String(formData.get(`just_reason__${ruleId}`) || ""),
      policy: String(formData.get(`just_policy__${ruleId}`) || ""),
    };
  }

  try {
    await postJson(`/review/${caseId}/gate`, {
      operator: String(formData.get("operator") || ""),
      rationale: String(formData.get("rationale") || ""),
      decision: String(formData.get("decision") || "aprobar"),
      justifications,
    });
  } catch (error) {
    return { ok: false, ...errorDetail(error) };
  }

  revalidatePath(`/review/${caseId}`);
  revalidatePath("/review");
  revalidatePath("/");
  return { ok: true, message: "Decisión registrada." };
}

export async function verifyAll() {
  try {
    const data = await postJson<{ report: { case_id: string; quarantined: boolean }[] }>(
      "/review/verify",
      {},
    );
    const quarantined = data.report.filter((entry) => entry.quarantined);
    revalidatePath("/");
    revalidatePath("/review");
    if (quarantined.length) {
      flash(
        "/review",
        `Retirados del portal público: ${quarantined.map((e) => e.case_id).join(", ")}.`,
        "warn",
      );
    }
    flash("/review", "Verificación correcta. Todas las decisiones están vigentes.");
  } catch (error) {
    const detail = errorDetail(error);
    flash("/review", detail.message, "err");
  }
}

export async function createProfile(
  _prev: ActionState,
  formData: FormData,
): Promise<ActionState> {
  const yaml = String(formData.get("yaml") || "");
  const overwrite = formData.get("overwrite") === "on";
  if (!yaml.trim()) {
    return { ok: false, message: "El formulario está vacío." };
  }
  try {
    const result = await postJson<{ profile_id: string }>("/profiles", {
      yaml,
      overwrite,
    });
    revalidatePath("/review");
    return { ok: true, profileId: result.profile_id, message: "Perfil guardado." };
  } catch (error) {
    return { ok: false, ...errorDetail(error) };
  }
}

export async function validateProfileYaml(yaml: string) {
  try {
    return await postJson<{
      valid: boolean;
      errors: { field: string; message: string }[];
    }>("/profiles/validate", { yaml });
  } catch (error) {
    const detail = errorDetail(error);
    return { valid: false, errors: detail.errors ?? [] };
  }
}
