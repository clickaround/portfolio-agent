# frontend

The portfolio workbench (React + Vite + TypeScript, to be built). Talks to `backend/api` only and codes against its contract `backend/api/openapi.json`; it never imports agent code.

Generate the typed client when the UI starts: `npx openapi-typescript ../backend/api/openapi.json -o src/api/schema.d.ts`.

## First screens (agreed scope: MVP workbench, no coordinate editing - the host LLM decides editorial things, rules execute)
1. **Projects**: list/create, brief editor (`/projects`, `/projects/{id}/brief`).
2. **Sources**: upload by kind, manifest table with transform badges (`source_transform`, `cutout`), before/after for prepare + cut-out (`/prepare`, `/cutout`, `/files/{kind}/{name}`).
3. **Book plan**: page list with role, assets, title, caption and the flags from `/catalog` (`bleed`, `dark`, `strip`, `photoset`, `focus`); "write with the host LLM" button (`/book-plan/generate`) with live job log; server-side validation errors shown per page.
4. **Pages**: compose (`/compose`), attempt grid of page PNGs, gate/advisory panel (codes -> pages/elements), PDF download.
5. **Review**: context -> reviewer paste/upload -> record -> finalize.

Open decisions: auth (none yet; localhost only), whether the editor later edits scene JSON directly (DesignCraft-first per the owner).
