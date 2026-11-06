# Portfolio Agent design map (v3)

## Product taxonomy
- A **portfolio** is a coherent, audience-appropriate selection and sequence of real project evidence; not a report template with identical cards.
- Shared core: source evidence → project and case analysis → editorial plan → format-aware page specification → backend-authorable editable layout → pixel/vector render → rule-based/semantic/human QA → scoped repair.
- Domain packs may enrich or override art-direction criteria, but the *document* representation doesn't know a hardcoded floor-plan/UX-screen field.
- Format specs define physical/digital dimensions, trim/bleed/safe, facing pages, asset minimum dpi, native vector policy and target export. All pages must derive dimensions from the active spec.

## Main module boundaries
| Location | Purpose | Must not own |
|---|---|---|
| `knowledge/domains/` | discipline-specific content, storytelling and critique | rendering geometry |
| `cases/` | rights-aware whole-portfolio exemplars, annotation, splits | third-party unlicensed binaries |
| `formats/` | page geometry, paper and digital preset/contracts | content semantics |
| `agents/` | optional parallel roles, typed handoffs, single writer | shared state concurrent writes |
| `skills/` | host-facing workflows (Codex, Claude) | proprietary editor runtime |
| `core/` | versioned portfolio, asset, scene, mutation contracts | arbitrary third-party vendor types |
| `backends/` | design/print/PPTX adapter boundary | permanent exclusive dependency |
| `benchmarks/` | independent quality/validity/cost/host comparisons | 'one beauty score' |
| `research/` | pinned GitHub audit/reproduction/rights risks | claims of runtime tests not run |
| `integrations/` | HarnessRouter UHP optional, output adapters | first MVP dependency |
| `tasks/` | canonical task DAG + evidence-defined cards | human memory guesses |

## One-page / book pipeline
1. Ingest supplied original file and immutable SHA ID; extract without editing source.
2. Inventory project media, claims, authorship and uncertainty; invalid claim → abstain/manual review.
3. Select reference cases by domain, purpose and medium with rights constraints; no leakage with held-out evaluation data.
4. Draft whole-book storyboard: why each page exists, intentional omissions, visual protagonist per page, page-to-page pacing.
5. Generate three different *layout strategies*, not three minor color swaps.
6. Select medium-appropriate backend (DTP, canvas, slides, HTML) behind an adapter contract.
7. Render and run hard gates + domain-specific review, repair only identified objects, recheck.
8. Export editable native and file outputs plus provenance/QA/change log.

## Core alternatives (decision not yet frozen)
A. Direct host → HTML/CSS/PDF (fast baseline). B. DesignCraft DTP pages (print). C. OpenPencil/FigCraft free canvas (graphic). D. GenOffice/DeckCraft (slides). E. One abstraction/scene model + backend adapters (scalable but high initial complexity). Benchmark A–D first, build E only for measurable multi-backend needs.


## Folders added during implementation (2026-11-04)
| path | role |
|---|---|
| `runtime/portfolio_agent/` | orchestration + local compositor (ADR-0007, fallback candidate) |
| `runtime/portfolio_agent/{core,authors,engine}/` | layered packages; rules in `runtime/ARCHITECTURE.md`, enforced by `tests/test_architecture.py` |
| `backends/<name>/adapter.py` | exporter/measurer adapters (local, designcraft); loaded by path via `engine/registry.py` |
| `knowledge/patterns/` | layout pattern data used by authors |
| `evidence/` | task evidence files + logs (`evidence/logs/`) |
| `preview/` | generated, gitignored review output (`scripts/preview.py`) |
| `benchmarks/reports/` | `<run-id>.json` run reports per PROTO_V3 |
