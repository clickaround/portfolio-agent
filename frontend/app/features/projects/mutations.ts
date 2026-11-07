import { api, unwrap } from "~/lib/api/client";

// WRITES (POST / PUT / DELETE). Used by `clientAction` in pages; they throw ApiError, the action turns it into form errors.

export async function createProject(input: { id: string; title?: string; brief?: string }) {
  return unwrap(await api.POST("/projects", { body: input }));
}

export async function deleteProject(projectId: string) {
  const res = await api.DELETE("/projects/{pid}", { params: { path: { pid: projectId } } });
  if (res.error !== undefined) unwrap(res as never);
}

export async function saveBrief(projectId: string, markdown: string) {
  return unwrap(await api.PUT("/projects/{pid}/brief", { params: { path: { pid: projectId } }, body: { markdown } }));
}
