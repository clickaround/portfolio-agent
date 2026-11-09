import { type RouteConfig, index, prefix, route } from "@react-router/dev/routes";

// File-based route CONFIG in the owner's wemake style: every page lives in features/<feature>/pages, a feature may own layouts/.
// A project is a workspace: one layout (header + tabs) and one page per workflow step, each page owned by its feature.
export default [
  index("common/pages/home-page.tsx"),
  ...prefix("auth", [
    route("login", "features/auth/pages/login-page.tsx"),
    route("join", "features/auth/pages/join-page.tsx"),
    route("callback", "features/auth/pages/callback-page.tsx"),
  ]),
  ...prefix("projects", [
    index("features/projects/pages/projects-page.tsx"),
    route(":projectId/editor/:attempt", "features/books/pages/editor-page.tsx"),
    // The layout owns the :projectId segment, so its tab links ("sources", "plan", ...) resolve under /projects/:projectId.
    route(":projectId", "features/projects/layouts/project-layout.tsx", [
      index("features/projects/pages/project-overview-page.tsx"),
      route("sources", "features/sources/pages/sources-page.tsx"),
      route("plan", "features/plans/pages/plan-page.tsx"),
      route("book", "features/books/pages/book-page.tsx"),
      route("review", "features/reviews/pages/review-page.tsx"),
    ]),
  ]),
] satisfies RouteConfig;
