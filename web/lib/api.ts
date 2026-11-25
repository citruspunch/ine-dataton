export const ENGINE_URL = process.env.ENGINE_URL ?? "http://127.0.0.1:8000";

export class EngineError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(`engine ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${ENGINE_URL}${path}`, {
    cache: "no-store",
    ...init,
  });
  if (!response.ok) {
    let detail: unknown = null;
    try {
      detail = await response.json();
    } catch {
      detail = await response.text();
    }
    throw new EngineError(response.status, detail);
  }
  return (await response.json()) as T;
}

export function getJson<T>(path: string): Promise<T> {
  return request<T>(path);
}

export function postJson<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function postForm<T>(path: string, form: FormData): Promise<T> {
  return request<T>(path, { method: "POST", body: form });
}

export function errorDetail(error: unknown): { errors?: { field: string; message: string }[]; message: string } {
  if (error instanceof EngineError) {
    const detail = error.detail as
      | { detail?: { errors?: { field: string; message: string }[] } | string }
      | null;
    if (detail && typeof detail === "object" && detail.detail) {
      if (typeof detail.detail === "string") {
        return { message: detail.detail };
      }
      if (Array.isArray(detail.detail.errors)) {
        return { errors: detail.detail.errors, message: "Errores de validación" };
      }
    }
    if (typeof error.detail === "string") {
      return { message: error.detail };
    }
    return { message: `El servicio de validación respondió ${error.status}` };
  }
  return { message: "No se pudo contactar el servicio de validación." };
}
