import { api, unwrap } from "~/lib/api/client";
import type { Manifest } from "./schema";

export async function getManifest(projectId: string) {
  const out = unwrap(await api.GET("/projects/{pid}/manifest", { params: { path: { pid: projectId } } }));
  return { manifest: out.manifest as unknown as Manifest, brief: out.brief };
}
