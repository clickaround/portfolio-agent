import { api, unwrap } from "~/lib/api/client";

// READS (GET). Used by `clientLoader` in pages; one function per endpoint, typed from backend/apps/api/openapi.json.

export async function getProjects() {
  return unwrap(await api.GET("/projects"));
}

export async function getProject(projectId: string) {
  return unwrap(await api.GET("/projects/{pid}", { params: { path: { pid: projectId } } }));
}

export async function getBrief(projectId: string) {
  return unwrap(await api.GET("/projects/{pid}/brief", { params: { path: { pid: projectId } } }));
}
