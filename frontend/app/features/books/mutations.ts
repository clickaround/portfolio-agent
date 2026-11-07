import { api, unwrap } from "~/lib/api/client";

export type ComposeInput = { width_mm: number; height_mm: number; margin_mm: number; bleed_mm: number; header: boolean };

/** Composes a new attempt from the plan in a background job. */
export async function composeBook(projectId: string, input: ComposeInput) {
  return unwrap(await api.POST("/projects/{pid}/compose", { params: { path: { pid: projectId } }, body: input }));
}
