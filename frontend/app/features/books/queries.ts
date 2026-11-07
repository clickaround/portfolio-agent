import { api, unwrap } from "~/lib/api/client";

export async function getAttempts(projectId: string) {
  return unwrap(await api.GET("/projects/{pid}/attempts", { params: { path: { pid: projectId } } }));
}
