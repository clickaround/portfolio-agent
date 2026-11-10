import createClient from "openapi-fetch";
import type { paths } from "~/types/api";
import { authenticatedFetch } from "~/lib/auth/fetch";

/** Typed client generated from backend/api/openapi.json (`npm run api:types`): paths, params and bodies are checked by the compiler. */
export const api = createClient<paths>({
  baseUrl: import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000",
  fetch: (request) => authenticatedFetch(request),
});

/** Shared connection to backend/apps/api. Per-feature calls live in features/<f>/queries.ts (reads) and mutations.ts (writes).
 *  The API answers errors as {error: {code, message}}; they become exceptions the route ErrorBoundary (or an action) can show. */
export class ApiError extends Error {
  code: string;
  status: number;
  constructor(code: string, message: string, status: number) {
    super(message);
    this.code = code;
    this.status = status;
  }
}

export function unwrap<T>(res: { data?: T; error?: unknown; response: Response }): T {
  if (res.error !== undefined || res.data === undefined) {
    const e = (res.error as { error?: { code?: string; message?: string } } | undefined)?.error;
    throw new ApiError(e?.code ?? "http_error", e?.message ?? `HTTP ${res.response.status}`, res.response.status);
  }
  return res.data;
}
