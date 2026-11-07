import { Link } from "react-router";
import { buttonVariants } from "~/common/components/ui/button";
import type { Route } from "./+types/home-page";

export const meta: Route.MetaFunction = () => [{ title: "Pascal" }, { name: "description", content: "Put in your sources; the agents arrange them into a portfolio." }];

export default function HomePage() {
  return (
    <div className="space-y-6 py-10">
      <h1 className="text-5xl font-extrabold tracking-tight">Pascal</h1>
      <p className="max-w-xl text-lg text-muted-foreground">
        Put in your photos, drawings and diagrams. The agents arrange and finish them into a portfolio, and every page stays tied to your originals.
      </p>
      <Link to="/projects" className={buttonVariants({ size: "lg" })}>Open projects</Link>
    </div>
  );
}
