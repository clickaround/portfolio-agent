import { Link, NavLink, Outlet } from "react-router";
import { Badge } from "~/common/components/ui/badge";
import { buttonVariants } from "~/common/components/ui/button";
import { cn } from "~/lib/utils";
import { getProject } from "../queries";
import type { Route } from "./+types/project-layout";

export const meta: Route.MetaFunction = ({ loaderData }) => [{ title: `${loaderData?.title || "Project"} | Pascal` }];

export async function clientLoader({ params }: Route.ClientLoaderArgs) {
  return getProject(params.projectId);
}

const tabs = [
  { to: "", label: "Overview", end: true },
  { to: "sources", label: "Sources" },
  { to: "plan", label: "Plan" },
  { to: "book", label: "Book" },
  { to: "review", label: "Review" },
];

/** Workflow shell for one project: header + tabs; each tab is a page of its own feature (sources / plans / books / reviews). */
export default function ProjectLayout({ loaderData }: Route.ComponentProps) {
  return (
    <div className="space-y-8">
      <div className="space-y-3">
        <Link to="/projects" className="text-sm text-primary">← Projects</Link>
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="text-4xl font-bold tracking-tight">{loaderData.title || loaderData.id}</h1>
          <Badge variant={loaderData.has_plan ? "default" : "outline"}>{loaderData.has_plan ? "plan ready" : "no plan"}</Badge>
          <Badge variant="outline">{loaderData.attempts} attempts</Badge>
        </div>
        <nav className="flex flex-wrap gap-2">
          {tabs.map((t) => (
            <NavLink key={t.label} to={t.to} end={t.end} className={({ isActive }) => cn(buttonVariants({ variant: isActive ? "secondary" : "ghost", size: "sm" }))}>
              {t.label}
            </NavLink>
          ))}
        </nav>
      </div>
      <Outlet context={{ project: loaderData }} />
    </div>
  );
}
