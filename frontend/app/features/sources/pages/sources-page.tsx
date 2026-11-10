import { AuthenticatedImage } from "~/common/components/authenticated-resource";
import { Form, useNavigation, useRevalidator } from "react-router";
import { JobProgress } from "~/common/components/job-progress";
import { Badge } from "~/common/components/ui/badge";
import { Button } from "~/common/components/ui/button";
import { Card } from "~/common/components/ui/card";
import { Input } from "~/common/components/ui/input";
import { ApiError } from "~/lib/api/client";
import { assetUrl } from "~/lib/api/urls";
import { cutoutAssets, deleteAsset, prepareSources, uploadAsset } from "../mutations";
import { getManifest } from "../queries";
import { ASSET_KINDS, type AssetKind } from "../schema";
import type { Route } from "./+types/sources-page";

export const meta: Route.MetaFunction = () => [{ title: "Sources | Pascal" }];

export async function clientLoader({ params }: Route.ClientLoaderArgs) {
  return { projectId: params.projectId, ...(await getManifest(params.projectId)) };
}

export async function clientAction({ request, params }: Route.ClientActionArgs) {
  const form = await request.formData();
  const intent = String(form.get("intent"));
  const pid = params.projectId;
  try {
    if (intent === "upload") {
      const kind = String(form.get("kind")) as AssetKind;
      const files = form.getAll("file").filter((f): f is File => f instanceof File && f.size > 0);
      if (files.length === 0) return { error: "Choose at least one file." };
      for (const f of files) await uploadAsset(pid, kind, f);
      return { ok: `${files.length} file(s) uploaded` };
    }
    const paths = form.getAll("path").map(String); // "<kind>/<file>" of the checked sources
    if (intent === "delete") {
      if (paths.length === 0) return { error: "Check at least one source." };
      for (const p of paths) {
        const [kind, ...name] = p.split("/");
        await deleteAsset(pid, kind as AssetKind, name.join("/"));
      }
      return { ok: `${paths.length} source(s) deleted` };
    }
    if (intent === "prepare" || intent === "approve") {
      const r = await prepareSources(pid, { approve: intent === "approve" });
      return { ok: `proposals ${r.proposals}, derived ${r.derived}${r.approved ? ", approved" : ""}` };
    }
    if (intent === "cutout") {
      const files = paths.filter((p) => p.startsWith("images/")).map((p) => p.slice("images/".length));
      if (files.length === 0) return { error: "Check at least one photo (images) for cut-out." };
      return { job: (await cutoutAssets(pid, files)).job };
    }
  } catch (e) {
    if (e instanceof ApiError) return { error: e.message };
    throw e;
  }
  return { error: `unknown action ${intent}` };
}

export default function SourcesPage({ loaderData, actionData }: Route.ComponentProps) {
  const { revalidate } = useRevalidator();
  const busy = useNavigation().state !== "idle";
  const assets = loaderData.manifest.assets;
  return (
    <section className="space-y-6">
      <Form method="post" encType="multipart/form-data" className="flex flex-wrap items-center gap-2">
        <input type="hidden" name="intent" value="upload" />
        <select name="kind" aria-label="kind" className="h-9 rounded-md border bg-background px-2 text-sm">
          {ASSET_KINDS.map((k) => <option key={k} value={k}>{k}</option>)}
        </select>
        <Input type="file" name="file" multiple accept="image/*" className="max-w-sm" aria-label="files" />
        <Button type="submit" disabled={busy}>Upload</Button>
      </Form>

      {actionData && "error" in actionData && <p role="alert" className="text-red-400">{actionData.error}</p>}
      {actionData && "ok" in actionData && <p className="text-sm text-muted-foreground">{actionData.ok}</p>}
      {actionData?.job && <JobProgress key={actionData.job} jobId={actionData.job} onDone={() => revalidate()} />}

      {assets.length === 0 ? (
        <p className="text-muted-foreground">No sources yet. Upload photos, drawings or diagrams.</p>
      ) : (
        <Form method="post" className="space-y-4">
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            {assets.map((a) => (
              <Card key={a.id} className="overflow-hidden">
                <AuthenticatedImage src={assetUrl(loaderData.projectId, a.relative_path)} alt={a.id} loading="lazy" className="aspect-square w-full bg-muted object-contain" />
                <div className="space-y-2 p-3 text-sm">
                  <label className="flex items-center gap-2 font-medium">
                    <input type="checkbox" name="path" value={a.relative_path} />
                    <span className="truncate">{a.id}</span>
                  </label>
                  <div className="flex flex-wrap gap-1">
                    <Badge variant="secondary">{a.role ?? a.kind}</Badge>
                    {a.width && a.height && <Badge variant="outline">{a.width}×{a.height}</Badge>}
                  </div>
                </div>
              </Card>
            ))}
          </div>
          <div className="flex flex-wrap gap-2">
            <Button type="submit" name="intent" value="prepare" variant="outline" disabled={busy}>Scan &amp; propose</Button>
            <Button type="submit" name="intent" value="approve" variant="outline" disabled={busy}>Approve proposals</Button>
            <Button type="submit" name="intent" value="cutout" variant="outline" disabled={busy}>Cut out checked</Button>
            <Button type="submit" name="intent" value="delete" variant="destructive" disabled={busy}>Delete checked</Button>
          </div>
        </Form>
      )}
    </section>
  );
}
