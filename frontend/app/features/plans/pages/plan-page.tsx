import { Form, useNavigation, useRevalidator } from "react-router";
import { JobProgress } from "~/common/components/job-progress";
import { Badge } from "~/common/components/ui/badge";
import { Button } from "~/common/components/ui/button";
import { ApiError } from "~/lib/api/client";
import { generatePlan, savePlan } from "../mutations";
import { getPlan } from "../queries";
import { planPages } from "../schema";
import type { Route } from "./+types/plan-page";

export const meta: Route.MetaFunction = () => [{ title: "Plan | Pascal" }];

export async function clientLoader({ params }: Route.ClientLoaderArgs) {
  return { plan: await getPlan(params.projectId) };
}

export async function clientAction({ request, params }: Route.ClientActionArgs) {
  const form = await request.formData();
  try {
    if (form.get("intent") === "generate") {
      const out = await generatePlan(params.projectId, { instructions: String(form.get("instructions") ?? ""), composeAfter: form.get("compose") === "on" });
      return { job: out.job };
    }
    let plan: Record<string, unknown>;
    try {
      plan = JSON.parse(String(form.get("plan")));
    } catch {
      return { error: "The plan is not valid JSON." };
    }
    const out = await savePlan(params.projectId, plan);
    return { ok: `saved: ${out.pages} pages, ${out.versions} earlier versions kept` };
  } catch (e) {
    if (e instanceof ApiError) return { error: e.message };
    throw e;
  }
}

export default function PlanPage({ loaderData, actionData }: Route.ComponentProps) {
  const { revalidate } = useRevalidator();
  const busy = useNavigation().state !== "idle";
  const pages = planPages(loaderData.plan);
  return (
    <section className="space-y-8">
      <Form method="post" className="space-y-3">
        <input type="hidden" name="intent" value="generate" />
        <h2 className="text-xl font-semibold">Let the host LLM write the plan</h2>
        <p className="text-sm text-muted-foreground">The LLM decides editorial things (page roles, flags, order). The layout rules place everything; no coordinates come from the LLM.</p>
        <textarea name="instructions" rows={3} placeholder="Optional guidance, e.g. lead with the site plan, dark section for night photos" className="w-full rounded-md border bg-background p-2 text-sm" />
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" name="compose" /> compose the book right after</label>
        <Button type="submit" disabled={busy}>Generate plan</Button>
      </Form>

      {actionData && "error" in actionData && <p role="alert" className="text-red-400">{actionData.error}</p>}
      {actionData && "ok" in actionData && <p className="text-sm text-muted-foreground">{actionData.ok}</p>}
      {actionData?.job && <JobProgress key={actionData.job} jobId={actionData.job} onDone={() => revalidate()} />}

      <Form method="post" className="space-y-3">
        <div className="flex items-center gap-2">
          <h2 className="text-xl font-semibold">Book plan</h2>
          {loaderData.plan ? <Badge variant="secondary">{pages.length} pages</Badge> : <Badge variant="outline">none yet</Badge>}
        </div>
        <ol className="space-y-2">
          {pages.map((p, i) => (
            <li key={i} className="flex flex-wrap items-center gap-2 rounded-md border p-3 text-sm">
              <span className="w-6 text-muted-foreground">{i + 1}</span>
              <Badge>{p.role}</Badge>
              {p.section && <Badge variant="outline">{p.section}</Badge>}
              <span className="min-w-0 flex-1 truncate font-medium">{p.title ?? p.tagline ?? ""}</span>
              {p.assets?.map((a) => <Badge key={a} variant="secondary">{a}</Badge>)}
              {p.flags?.map((f) => <Badge key={f} variant="outline">{f}</Badge>)}
            </li>
          ))}
        </ol>
        <details className="space-y-2">
          <summary className="cursor-pointer text-sm text-muted-foreground">Edit the plan as JSON</summary>
        <textarea
          name="plan"
          key={JSON.stringify(loaderData.plan)}
          defaultValue={loaderData.plan ? JSON.stringify(loaderData.plan, null, 1) : ""}
          rows={16}
          spellCheck={false}
          placeholder='{"pages": [...]}'
          className="w-full rounded-md border bg-background p-2 font-mono text-xs"
        />
        </details>
        <Button type="submit" variant="outline" disabled={busy}>Save plan</Button>
      </Form>
    </section>
  );
}
