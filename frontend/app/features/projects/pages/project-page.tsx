import { Link } from "react-router";
import { api, unwrap } from "~/lib/api-client";
import type { Route } from "./+types/project-page";

export const meta: Route.MetaFunction = ({ loaderData }) => [{ title: `${loaderData?.title ?? "Project"} | Pascal` }];

export async function clientLoader({ params }: Route.ClientLoaderArgs) {
  return unwrap(await api.GET("/projects/{pid}", { params: { path: { pid: params.projectId } } }));
}

/** Project workspace shell. Sources / Plan / Pages / Review are separate features composed under this route (see README). */
export default function ProjectPage({ loaderData }: Route.ComponentProps) {
  const a = loaderData.assets;
  return (
    <section className="mx-auto max-w-5xl space-y-4 p-6">
      <Link to="/" className="text-sm text-accent">← Projects</Link>
      <h1 className="font-serif text-3xl">{loaderData.title || loaderData.id}</h1>
      <p className="text-ink/60">{a.images} images · {a.drawings} drawings · {a.diagrams} diagrams · plan: {loaderData.has_plan ? "yes" : "no"} · attempts: {loaderData.attempts}</p>
    </section>
  );
}
