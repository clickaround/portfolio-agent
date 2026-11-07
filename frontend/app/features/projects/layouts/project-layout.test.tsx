import { render, screen } from "@testing-library/react";
import { createRoutesStub } from "react-router";
import { describe, expect, it } from "vitest";
import ProjectLayout from "./project-layout";

// Regression: the tab links are relative ("sources", "plan"...). They must resolve under /projects/:projectId, not under the app root.
describe("ProjectLayout tabs", () => {
  it("links every tab below the project path", async () => {
    const project = { id: "demo", title: "Demo", assets: { images: 0, drawings: 0, diagrams: 0 }, has_plan: false, attempts: 0 };
    const Stub = createRoutesStub([
      {
        path: "/projects/:projectId",
        Component: ProjectLayout as never,
        loader: () => project,
        children: [{ index: true, Component: () => <p>overview</p> }, { path: "plan", Component: () => <p>plan page</p> }],
      },
    ]);
    render(<Stub initialEntries={["/projects/demo"]} />);
    expect((await screen.findByRole("link", { name: "Plan" })).getAttribute("href")).toBe("/projects/demo/plan");
    expect(screen.getByRole("link", { name: "Sources" }).getAttribute("href")).toBe("/projects/demo/sources");
    expect(screen.getByRole("link", { name: "Overview" }).getAttribute("href")).toBe("/projects/demo");
  });
});
