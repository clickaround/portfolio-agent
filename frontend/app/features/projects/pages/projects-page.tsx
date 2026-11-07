import { Form, Link, redirect } from "react-router";
import { Badge } from "~/common/components/ui/badge";
import { Button } from "~/common/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "~/common/components/ui/card";
import { Input } from "~/common/components/ui/input";
import { ApiError } from "~/lib/api/client";
import { createProject } from "../mutations";
import { getProjects } from "../queries";
import type { Route } from "./+types/projects-page";

export const meta: Route.MetaFunction = () => [{ title: "Projects | Pascal" }];

export async function clientLoader() {
  return getProjects();
}

export async function clientAction({ request }: Route.ClientActionArgs) {
  const id = String((await request.formData()).get("id") ?? "").trim();
  try {
    await createProject({ id, title: id });
  } catch (e) {
    if (e instanceof ApiError) return { error: e.message };
    throw e;
  }
  return redirect(`/projects/${id}`);
}

export default function ProjectsPage({ loaderData, actionData }: Route.ComponentProps) {
  return (
    <section className="mx-auto max-w-3xl space-y-8">
      <div className="space-y-2">
        <h1 className="text-4xl font-bold tracking-tight">Projects</h1>
        <p className="text-muted-foreground">Put in your sources; the agents arrange them into a portfolio.</p>
      </div>
      <Form method="post" className="flex gap-2">
        <Input name="id" aria-label="project id" placeholder="new-project-id (a-z, 0-9, - _)" pattern="[a-z0-9][a-z0-9_\-]{0,63}" required />
        <Button type="submit">Create</Button>
      </Form>
      {actionData?.error && <p role="alert" className="text-red-400">{actionData.error}</p>}
      <div className="space-y-3">
        {loaderData.map((p) => (
          <Link key={p.id} to={`/projects/${p.id}`} className="block">
            <Card className="transition-colors hover:bg-accent/40">
              <CardHeader className="flex-row items-center justify-between space-y-0">
                <div className="space-y-1">
                  <CardTitle>{p.title || p.id}</CardTitle>
                  <CardDescription>{p.assets.images + p.assets.drawings + p.assets.diagrams} assets · {p.attempts} attempts</CardDescription>
                </div>
                {p.has_plan && <Badge variant="secondary">plan</Badge>}
              </CardHeader>
            </Card>
          </Link>
        ))}
        {loaderData.length === 0 && <p className="text-muted-foreground">No projects yet.</p>}
      </div>
    </section>
  );
}
