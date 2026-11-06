import { Form, Link, redirect } from "react-router";
import { Button } from "~/common/components/ui/button";
import { api, ApiError, unwrap } from "~/lib/api-client";
import type { Route } from "./+types/projects-page";

export const meta: Route.MetaFunction = () => [{ title: "Projects | Pascal" }];

export async function clientLoader() {
  return unwrap(await api.GET("/projects"));
}

export async function clientAction({ request }: Route.ClientActionArgs) {
  const id = String((await request.formData()).get("id") ?? "").trim();
  try {
    unwrap(await api.POST("/projects", { body: { id, title: id } }));
  } catch (e) {
    if (e instanceof ApiError) return { error: e.message };
    throw e;
  }
  return redirect(`/projects/${id}`);
}

export default function ProjectsPage({ loaderData, actionData }: Route.ComponentProps) {
  return (
    <section className="mx-auto max-w-3xl space-y-6 p-6">
      <h1 className="font-serif text-3xl">Projects</h1>
      <Form method="post" className="flex gap-2">
        <input
          name="id"
          aria-label="project id"
          placeholder="new-project-id (a-z, 0-9, - _)"
          pattern="[a-z0-9][a-z0-9_\-]{0,63}"
          required
          className="flex-1 rounded-md border border-rule bg-white px-3 py-1.5"
        />
        <Button type="submit">Create</Button>
      </Form>
      {actionData?.error && <p role="alert" className="text-accent">{actionData.error}</p>}
      <ul className="divide-y divide-rule rounded-md border border-rule bg-white">
        {loaderData.map((p) => (
          <li key={p.id} className="flex items-center justify-between p-3">
            <Link className="font-medium hover:text-accent" to={`/projects/${p.id}`}>{p.title || p.id}</Link>
            <span className="text-sm text-ink/60">{p.assets.images + p.assets.drawings + p.assets.diagrams} assets · {p.attempts} attempts</span>
          </li>
        ))}
        {loaderData.length === 0 && <li className="p-3 text-ink/60">No projects yet.</li>}
      </ul>
    </section>
  );
}
