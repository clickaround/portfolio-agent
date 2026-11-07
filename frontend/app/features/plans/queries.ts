import { api, ApiError, unwrap } from "~/lib/api/client";

/** The book plan as JSON, or null when the project has none yet (the API answers 404 no_plan). */
export async function getPlan(projectId: string): Promise<Record<string, unknown> | null> {
  try {
    return unwrap(await api.GET("/projects/{pid}/book-plan", { params: { path: { pid: projectId } } })) as Record<string, unknown>;
  } catch (e) {
    if (e instanceof ApiError && e.code === "no_plan") return null;
    throw e;
  }
}
