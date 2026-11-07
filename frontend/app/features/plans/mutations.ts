import { api, unwrap } from "~/lib/api/client";

/** Validated by the backend (schema + the planned author's asset rules); the previous plan is kept there. */
export async function savePlan(projectId: string, plan: Record<string, unknown>) {
  return unwrap(await api.PUT("/projects/{pid}/book-plan", { params: { path: { pid: projectId } }, body: plan }));
}

/** The host LLM writes the plan in a background job. `composeAfter` also composes the book once it is written. */
export async function generatePlan(projectId: string, input: { instructions: string; composeAfter: boolean }) {
  return unwrap(
    await api.POST("/projects/{pid}/book-plan/generate", {
      params: { path: { pid: projectId } },
      body: { instructions: input.instructions, compose: input.composeAfter ? {} : null },
    }),
  );
}
