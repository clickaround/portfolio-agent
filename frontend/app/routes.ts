import { type RouteConfig, index, layout, prefix, route } from "@react-router/dev/routes";

// File-based route CONFIG (the owner's feature-folder convention): every page is a file under features/<feature>/pages.
// Planned features (see README): sources, plan, book, review - each gets its own folder and its routes under projects/:projectId.
export default [
  layout("common/layouts/app-layout.tsx", [
    index("features/projects/pages/projects-page.tsx"),
    ...prefix("projects", [route(":projectId", "features/projects/pages/project-page.tsx")]),
  ]),
] satisfies RouteConfig;
