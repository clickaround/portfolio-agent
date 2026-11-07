import type { components } from "~/types/api";

export type Project = components["schemas"]["ProjectInfo"];
/** What project-layout hands to its tab pages through <Outlet context>. */
export type ProjectContext = { project: Project };
