import { authClient } from "./client";

/** Send the current Supabase access token without exposing it in resource URLs. */
export async function authenticatedFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const session = await authClient?.auth.getSession();
  const token = session?.data.session?.access_token;
  if (!token) return globalThis.fetch(input, init);
  const url = typeof input === "string" ? new URL(input, window.location.origin) : input;
  const request = new Request(url, init);
  request.headers.set("Authorization", `Bearer ${token}`);
  return globalThis.fetch(request);
}
