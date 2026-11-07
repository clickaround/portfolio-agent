import { api, unwrap } from "~/lib/api/client";

// The engine never judges taste: bind frames and hashes for a FRESH reviewer, record its verdict, then finalize.

export async function bindReviewContext(projectId: string) {
  return unwrap(await api.POST("/projects/{pid}/review/context", { params: { path: { pid: projectId } } }));
}

export async function recordReview(projectId: string, review: Record<string, unknown>) {
  return unwrap(await api.POST("/projects/{pid}/review/record", { params: { path: { pid: projectId } }, body: { review } }));
}

/** Promotes the latest attempt to final only if blocking gates passed AND a fresh review passed. */
export async function finalizeBook(projectId: string) {
  return unwrap(await api.POST("/projects/{pid}/review/finalize", { params: { path: { pid: projectId } } }));
}
