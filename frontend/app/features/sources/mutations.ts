import { api, unwrap } from "~/lib/api/client";
import { uploadProjectAsset } from "~/lib/api/assets";
import type { AssetKind } from "./schema";

export async function uploadAsset(projectId: string, kind: AssetKind, file: File) {
  return uploadProjectAsset(projectId, kind, file);
}

export async function deleteAsset(projectId: string, kind: AssetKind, name: string) {
  const res = await api.DELETE("/projects/{pid}/assets/{kind}/{name}", { params: { path: { pid: projectId, kind, name } } });
  if (res.error !== undefined) unwrap(res as never);
}

/** Scan sources and write proposals; `approve` accepts them. Synchronous on the backend. */
export async function prepareSources(projectId: string, input: { approve?: boolean; levels?: boolean; knockout?: boolean }) {
  return unwrap(await api.POST("/projects/{pid}/prepare", { params: { path: { pid: projectId } }, body: input }));
}

/** Background cut-out; answers a job id. */
export async function cutoutAssets(projectId: string, files: string[]) {
  return unwrap(await api.POST("/projects/{pid}/cutout", { params: { path: { pid: projectId } }, body: { files } }));
}
