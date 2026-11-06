# Product goals and non-goals — v0.4.0

## Product
**Portfolio Agent**: domain-aware editorial portfolio authoring, editable document outputs, print/presentation/digital formats, research-backed reference retrieval, and reproducible quality checks. Distribution first as Claude Code / Codex Skills + portable plugin; an optional local CLI/backends, not a large custom web SaaS at the start.

## User jobs
- Provide raw assets (renderings, CAD-derived PDFs, UX screens, photos, brand work, product images, project notes, code/research figures).
- State target audience, portfolio objective, domain(s), output medium, physical/digital dimensions, and length.
- Receive ranked project/content selection, narrative storyboard, 2–3 genuinely different editorial layout directions, polished pages, editable source, export and QA report.
- Revise one image/page/caption without unrelated page drift; rerender at alternative sizes without silently losing text or cropping critical assets.

## Success gates
1. Facts and essential visuals maintain traceable provenance; source files remain immutable.
2. Real reference cases with lawful scope are used and their *principles* abstracted, not copied.
3. Page size, bleed, trim, margins, gutters, facing pages, photo resolution and text fit obey declared constraints.
4. Local edit operations produce a scoped diff and preserve unrelated objects.
5. Professional review judges outputs better than a direct-host baseline on pre-registered criteria; report negative and neutral results honestly.
6. Both direct Claude Code and direct Codex paths can discover the same Skills after separate host verification.
7. Time/cost to completion and user's manual editing time are measured; no unverified monetization claims.

## Initial vertical slice
One real permitted case from one domain + a synthetic safe fallback, 2 pages of arbitrary page preset (not hardwired A3), 3 layout candidates, editable source, PDF/PNG preview, hard-gate report, 1 scoped edit. Choose the first domain in `knowledge/domains/` after case availability; architecture is a useful first fixture, **not the global product schema**.

## Non-goals in V0
Foundation model training, large scale scraping, bespoke Figma clone, native CAD/BIM authoring, full Adobe app equivalence, guaranteed PDF/X certification without measured backend evidence, multi-tenant cloud backend, mandatory HarnessRouter orchestration, uncontrolled parallel agents, indiscriminate merging of third-party source trees.

## Architecture status
No editing backend is chosen. DesignCraft, OpenPencil, GenOffice, HTML/Paged.js, PhotoCraft/VectorCraft are research candidates with distinct roles. Core interfaces freeze only after practical spikes.
