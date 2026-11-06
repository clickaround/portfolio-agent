import { render, screen } from "@testing-library/react";
import { createRoutesStub } from "react-router";
import { afterEach, expect, it, vi } from "vitest";
import ProjectsPage, { clientLoader } from "./projects-page";

afterEach(() => vi.restoreAllMocks());

const json = (body: unknown, status = 200) => new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });

function renderPage() {
  // The page is rendered exactly as the router does: its clientLoader result arrives as `loaderData`.
  const Stub = createRoutesStub([{ path: "/", Component: ProjectsPage as never, loader: () => clientLoader() }]);
  return render(<Stub initialEntries={["/"]} />);
}

it("lists the projects the API returns", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(json([{ id: "robie", title: "Robie House", assets: { images: 3, drawings: 8, diagrams: 4 }, has_plan: true, attempts: 2 }]));
  renderPage();
  expect(await screen.findByText("Robie House")).toBeInTheDocument();
  expect(screen.getByText(/15 assets · 2 attempts/)).toBeInTheDocument();
});

it("an empty list says so", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(json([]));
  renderPage();
  expect(await screen.findByText("No projects yet.")).toBeInTheDocument();
});
