"use client";

import { useCallback, useEffect, useState } from "react";

// Empty in the built app (same origin as the API); set NEXT_PUBLIC_API_URL=http://localhost:8000
// when running `next dev` against a separately started backend.
export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

export class ApiError extends Error {
  constructor(message: string, public status: number, public field?: string) {
    super(message);
  }
}

type Options = Omit<RequestInit, "body"> & { json?: unknown; body?: BodyInit };

export async function api<T>(path: string, options: Options = {}): Promise<T> {
  const { json, headers: given, ...rest } = options;
  const headers = new Headers(given);
  let body = options.body;
  if (json !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(json);
  }
  const response = await fetch(API_BASE + path, { ...rest, headers, body, credentials: "include" });
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    let field: string | undefined;
    try {
      const data = await response.json();
      const detail = data.detail;
      if (typeof detail === "string") message = detail;
      else if (detail?.message) {
        message = detail.message;
        field = detail.field;
      } else if (Array.isArray(detail)) {
        message = detail.map((e: { loc?: string[]; msg: string }) => `${e.loc?.at(-1) ?? "input"}: ${e.msg}`).join("; ");
      }
    } catch {
      // keep the generic message
    }
    throw new ApiError(message, response.status, field);
  }
  const type = response.headers.get("content-type") ?? "";
  return (type.includes("application/json") ? response.json() : response.text()) as Promise<T>;
}

/** Fetch JSON on mount (and whenever `path` changes); `reload` fetches again. */
export function useApi<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState(path !== null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (path === null) return;
    let cancelled = false;
    setLoading(true);
    api<T>(path)
      .then((result) => {
        if (!cancelled) {
          setData(result);
          setError(null);
        }
      })
      .catch((err: ApiError) => !cancelled && setError(err))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, [path, tick]);

  const reload = useCallback(() => setTick((t) => t + 1), []);
  return { data, error, loading, reload };
}
