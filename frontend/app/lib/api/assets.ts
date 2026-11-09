import { api, unwrap } from "./client";

export type AssetKind = "images" | "drawings" | "diagrams";

/** Upload one source into the project's existing asset API. */
export async function uploadProjectAsset(projectId: string, kind: AssetKind, file: File) {
  const body = new FormData();
  body.append("file", file);
  return unwrap(await api.POST("/projects/{pid}/assets/{kind}", {
    params: { path: { pid: projectId, kind } },
    body: body as never,
    bodySerializer: (value) => value as never,
  }));
}
