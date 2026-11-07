import { Form, redirect, useNavigation, useOutletContext } from "react-router";
import { Button } from "~/common/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "~/common/components/ui/card";
import { ApiError } from "~/lib/api/client";
import { deleteProject, saveBrief } from "../mutations";
import { getBrief } from "../queries";
import type { ProjectContext } from "../schema";
import type { Route } from "./+types/project-overview-page";

export const meta: Route.MetaFunction = () => [{ title: "Overview | Pascal" }];

export async function clientLoader({ params }: Route.ClientLoaderArgs) {
  return { brief: (await getBrief(params.projectId)).markdown };
}

export async function clientAction({ request, params }: Route.ClientActionArgs) {
  const form = await request.formData();
  try {
    if (form.get("intent") === "delete") {
      await deleteProject(params.projectId);
      return redirect("/projects");
    }
    await saveBrief(params.projectId, String(form.get("brief") ?? ""));
    return { ok: "Brief saved." };
  } catch (e) {
    if (e instanceof ApiError) return { error: e.message };
    throw e;
  }
}

export default function ProjectOverviewPage({ loaderData, actionData }: Route.ComponentProps) {
  const { project } = useOutletContext<ProjectContext>();
  const busy = useNavigation().state !== "idle";
  const a = project.assets;
  return (
    <div className="space-y-8">
      <div className="grid gap-4 sm:grid-cols-3">
        {([["Images", a.images], ["Drawings", a.drawings], ["Diagrams", a.diagrams]] as const).map(([label, n]) => (
          <Card key={label}>
            <CardHeader><CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle></CardHeader>
            <CardContent className="text-3xl font-semibold">{n}</CardContent>
          </Card>
        ))}
      </div>

      <Form method="post" className="space-y-3">
        <h2 className="text-xl font-semibold">Brief</h2>
        <p className="text-sm text-muted-foreground">The only text the plan may draw facts from (project.md). Title, audience, keywords and sections go here.</p>
        <textarea name="brief" key={loaderData.brief} defaultValue={loaderData.brief} rows={14} className="w-full rounded-md border bg-background p-2 font-mono text-sm" />
        <Button type="submit" disabled={busy}>Save brief</Button>
        {actionData && "ok" in actionData && <span className="ml-3 text-sm text-muted-foreground">{actionData.ok}</span>}
        {actionData && "error" in actionData && <p role="alert" className="text-red-400">{actionData.error}</p>}
      </Form>

      <Form method="post" className="space-y-2 rounded-md border border-red-400/30 p-4">
        <input type="hidden" name="intent" value="delete" />
        <h2 className="font-semibold">Delete project</h2>
        <p className="text-sm text-muted-foreground">Removes the sources, plan and every attempt from the server. This cannot be undone.</p>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" required /> I understand</label>
        <Button type="submit" variant="destructive" disabled={busy}>Delete project</Button>
      </Form>
    </div>
  );
}
