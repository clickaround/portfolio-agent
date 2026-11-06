> **ARCHIVED V2 CONTEXT — non-authoritative.** Current: `AGENTS.md`, `GOALS.md`, `PLANS.md`, `architecture/ARCHITECTURE_MAP.md`, `research/repos.lock.json`, `formats/`.

# Architecture Proposal v0.2 — evidence-sensitive, NOT FROZEN

Superseded structural risk/alternatives are in `architecture/ALTERNATIVES_V2.md`; do not freeze this design until P04 probes and P05 ADR.

## C4: System context
Actors: portfolio author (owns materials), designer/reviewer (assesses work), Claude Code/Codex host (executes Skills and tools), external design backends (editable artifacts), optional HarnessRouter (unified harness API). External reference source links supply data with explicit rights, never instructions.

```
User assets + destination rules + case library
     ↓
Host Agent (Claude Code or Codex)
   ├── portfolio-research Skill → rights-approved case annotations
   ├── portfolio-plan Skill     → AssetManifest + BookPlan + DesignProfile
   ├── layout backend adapter   → SceneDocument/editable native file
   └── portfolio-review Skill   → deterministic checks + independent visual critic
                        ↓
              editable source + PDF + QA report
```

## C4: Logical components (no premature services)
- `CaseRepository`: references to authorized case metadata, full portfolio sequence and page annotations. Retrieval by **domain × purpose × page role × asset mix**. Later embeddings only if tag retrieval fails.
- `AssetInventory`: immutable source files, hashes, type, dimensions, page numbers, rights; detect drawings vs renders vs diagrams with confidence/evidence.
- `StoryPlanner`: inputs purpose + assets + domain pack + references; outputs `BookPlan` defining why each spread exists, what is omitted. Never guesses unknown facts.
- `DesignDirector`: synthesizes small style tokens and composition constraints, not pixel coordinates. References are inspiration, no copying.
- `LayoutAdapter` interface: `inspect_capabilities`, `create_document`, `place_assets`, `apply_patch`, `render_preview`, `export_pdf`, `open_editable`, `audit`. OpenPencil/GenOffice/local PDF as **independent candidates**.
- `SourceGuard`: verifies immutable bytes, allowed transforms, crop permission, labels, provenance, linework zoom quality.
- `QualityHarness`: deterministic hard gates first, domain-aware visual critique and human preference second. Only scoped repairs allowed.
- `RunLedger`: input hashes, config/model/host, backend, actions, output version, costs, test results.

## Main data flow
1. Ingest source via `AssetManifest` (never overwrite uploaded assets).
2. Load domain policy, target medium and recipient rules (check AI-disclosure/prohibition and submission size requirements).
3. Retrieve 2–3 permitted references with provenance; show *why* they match.
4. Output `BookPlan` with page purpose, narrative, asset placement hierarchy, facts linked to source IDs, risk list.
5. Generate multiple layout candidates through a **verified** backend. Keep native document and independent Scene JSON or change log.
6. Render for audit; pass hard gates (validity/fidelity), then visual + human selection. Repair only known elements; record diff.
7. Export print PDF, test against preview at zoom/page size; keep editable source and output manifest.

## Alternatives under test (ADD/ATAM)
A. Agent direct HTML/CSS: fast, visually flexible, fragile local edit and PDF fidelity. Always retain as B0 baseline.
B. Native design backend objects (OpenPencil) controlled by CLI/MCP: possibly editable and inspectable; source-PDF import unknown.
C. Native PPTX/Office backend (GenOffice): possibly easier editable delivery; A3 portfolio and vector linework unknown.
D. Hybrid restricted source PDF compositing: precise linework potential; requires custom positioning/review and may not yield natively editable drawing contents.
**No committed winner before P04 evidence.** Document each tradeoff in ADR and `benchmarks/`.

## Failure model and recovery
- Unknown asset: reject plan and ask for evidence; no placeholder claim.
- Source PDF preview differs from export: hard fail, switch to safer compositing or retain original PDF as attachment/opaque placed object.
- Layout invalid: identify IDs; patch only those and log diff, max N retries from config; no uncontrolled retries.
- Host CLI/MCP absent: mark `BACKEND_NOT_AVAILABLE`, offer permitted fallback, do not claim output complete.
- Reference rights unresolved: store link metadata only, do not copy asset pixels.
- Model/prompt attack from source file: source is untrusted, never run embedded shell/network instructions.
- Export failure: retain scene and editable file, present clear failure and paths; do not fake PDF.

## Platform, costs and scope
No standalone Next.js, Supabase, custom web editor, or own MCP server at P00. Local filesystem first. HarnessRouter is **optional runtime comparison** (P08), not the plugin's dependency. Small deterministic scripts belong in `scripts/`, external backend adapters only after proven. Commercial web UI may be a separate later product.
