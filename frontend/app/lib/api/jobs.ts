import { api, unwrap } from "./client";

/** Long operations (compose, plan generation, cut-out) answer 202 {job}; poll it here. Shared by several features, so it lives in lib/api. */
export async function getJob(jobId: string) {
  return unwrap(await api.GET("/jobs/{jid}", { params: { path: { jid: jobId } } }));
}
