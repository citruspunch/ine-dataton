"use client";

import { useEffect, useState } from "react";
import type {
  Meta,
  MunicipalitiesPayload,
  Profile,
} from "@/lib/types";

const profileCache = new Map<string, Profile>();

async function fetchJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(path, { signal, cache: "force-cache" });
  if (!response.ok) {
    throw new Error(
      response.status === 404
        ? "No se encontraron los datos procesados. Ejecuta `uv run municipal-profile all`."
        : `No se pudo cargar ${path} (HTTP ${response.status}).`,
    );
  }
  return (await response.json()) as T;
}

export function useBootstrap() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [territories, setTerritories] =
    useState<MunicipalitiesPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    Promise.all([
      fetchJson<Meta>("/data/meta.json"),
      fetchJson<MunicipalitiesPayload>("/data/municipalities.json"),
    ])
      .then(([nextMeta, nextTerritories]) => {
        if (!active) return;
        setMeta(nextMeta);
        setTerritories(nextTerritories);
      })
      .catch((cause: unknown) => {
        if (!active) return;
        setError(cause instanceof Error ? cause.message : "Error desconocido");
      });
    return () => {
      active = false;
    };
  }, []);

  return { meta, territories, error };
}

export function useProfile(code: string | null, enabled: boolean) {
  const [result, setResult] = useState<{
    code: string | null;
    profile: Profile | null;
    error: string | null;
  }>({ code: null, profile: null, error: null });

  useEffect(() => {
    if (!code || !enabled) return;

    const cached = profileCache.get(code);
    if (cached) return;

    const controller = new AbortController();

    fetchJson<Profile>(`/data/profiles/${code}.json`, controller.signal)
      .then((nextProfile) => {
        profileCache.set(code, nextProfile);
        setResult({ code, profile: nextProfile, error: null });
      })
      .catch((cause: unknown) => {
        if (controller.signal.aborted) return;
        setResult({
          code,
          profile: null,
          error: cause instanceof Error ? cause.message : "Error desconocido",
        });
      });

    return () => controller.abort();
  }, [code, enabled]);

  const cached = code ? (profileCache.get(code) ?? null) : null;
  const active = result.code === code;
  const profile = active ? result.profile ?? cached : cached;
  const failed = active && !profile && Boolean(result.error);
  const error = failed ? result.error : null;
  const loading = Boolean(code && enabled && !profile && !failed);

  return { profile, loading, error };
}
