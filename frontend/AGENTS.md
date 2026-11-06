# frontend - agent instructions (Claude Code / Codex / Cursor)

Stack: React Router 8 framework mode (SPA) + Vite 8 + Tailwind CSS 4 + shadcn/ui + TypeScript. Structure and page conventions: `README.md` (read it first). Backend contract: `../backend/apps/api/openapi.json` -> `npm run api:types`.

- Use the `function` keyword for pure functions, named exports for components, default export for pages, descriptive names with auxiliary verbs (`isLoading`, `hasError`), lowercase-dash directories, declarative JSX, interfaces over types, no enums.
- New page: file in `app/features/<feature>/pages/<name>-page.tsx` + entry in `app/routes.ts`; export `meta`, `clientLoader`, `clientAction` (if it writes); component takes `Route.ComponentProps` (`loaderData`, `actionData`).
- Imports: `react-router` only; shadcn UI from `~/common/components/ui`; never Radix, never `@remix-run`, never `react-router-dom`; no cross-feature imports (ESLint enforces).
- Tailwind v4: tokens in `app/app.css` `@theme`; do not create `tailwind.config.*` or `postcss.config.*`.
- Before finishing: `npm run typecheck && npm run lint && npm test && npm run build`.
- The owner decides editorial matters in the book plan; the UI never computes layout coordinates.
