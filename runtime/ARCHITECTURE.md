# runtime/ — module architecture (maintainers' guide)

Status: implemented vertical slice under ADR-0007 / ADR-0008 (PROPOSED). Enforced by `tests/test_architecture.py`.

## Layers and the one dependency rule
```
core  <-  layout  <-  authors/*, backends/*  <-  engine  <-  cli
```
A layer may import only layers to its left. Nothing imports `cli`. Authors never import each other. Backends never import each other or `engine`.
Only `engine/registry.py` knows concrete authors/backends; everything else talks to the `Protocol`s in `core/contracts.py`.

| Layer | Path | Owns | Must NOT contain |
|---|---|---|---|
| core | `runtime/portfolio_agent/core/` | contracts (Protocols), asset ingest + hashing, brief parsing, geometry, naming conventions, diagnostics, plugin paths; **`core/guardrails/`** = policy (blocking/advisory), gates, grounding, bounded repair, reference-rights gate | layout generation, rendering, domain knowledge, backend names |
| layout | `runtime/portfolio_agent/layout/` | deterministic composition primitives: column grid, type system (`typesystem.py`), page compositions (`compositions.py`), guillotine solver (`treelayout.py`), plan->scenes (`book.py`). Rules cited in `knowledge/editorial/layout-craft.md` | editorial decisions (which asset where, words), domain knowledge, export |
| authors | `runtime/portfolio_agent/authors/<name>/` | turning brief + assets + spec into a plan + scenes (rule-based, host-authored, future ones) | file export, QA rules, CLI |
| backends | `backends/<name>/adapter.py` (outside the package) | measuring text and exporting scenes to files (PDF/PPTX/native/IDML), one folder per tool | layout decisions, gates |
| engine | `runtime/portfolio_agent/engine/` | orchestration (`pipeline`), local-edit proof (`edit`), blind candidates, spec/design-plan translation, registry | layout, rendering, domain rules |
| cli | `runtime/portfolio_agent/cli.py` | argument parsing only | logic |

## Where things live (not in code)
- Domain knowledge: `knowledge/domains/*.md`, layout patterns `knowledge/patterns/layout-patterns.json` (data, never inside the package; test enforces).
- Schemas/contracts: `contracts/*.schema.json`, `formats/`. Format presets: `formats/page-presets.json`.
- Skills (host-facing workflows): `skills/*/SKILL.md`. Design decisions: `architecture/adr/`. Evidence: `evidence/`. Benchmarks: `benchmarks/` (+ `benchmarks/reports/`).
- Third-party code is NEVER vendored: `.cache/vendor` (pinned clones, ignored), `.cache/bin` (verified binaries, ignored).

## Data crossing layers (plain dicts, JSON-able)
`manifest` (immutable assets + sha256) -> `brief` -> `plan` (author-defined pages + `meta`) -> `scene` per page (mm, `contracts/scene-document.schema.json`) -> exported files + `qa.json`.
Element id conventions shared by authors/backends/gates: `title-NN` (bold heading), `body-NN`, `caption-NN`, `photo-NN-k`, `drawing-NN-k`, `folio-NN`/`rule-NN` (footer). See `core/conventions.py`.

## How to extend (each is a local change)
- **New backend** (e.g. OpenPencil, GenOffice): add `backends/<name>/adapter.py` defining `BACKEND` with `name`, `capabilities`, `export(...)` (and `configure/text_fits` only if it can measure its own text). Imports only `portfolio_agent.core`. Add a spike evidence file first (`evidence/<NAME>_PROBE.md`); the architecture test checks the file shape.
- **New author** (e.g. an LLM page planner): add `runtime/portfolio_agent/authors/<name>/__init__.py` defining `AUTHOR` with `propose()` (and `relayout()` if `can_relayout`). Imports only `core`. Register nothing: `registry.get_author("<name>")` resolves it by package name.
- **New domain**: knowledge + patterns only (`knowledge/domains/<domain>.md`, entries in `layout-patterns.json`, a fixture under `examples/`). No code change; if one is needed, the abstraction is wrong.
- **New output format/size**: `formats/page-presets.json` + spec fields; geometry is in mm everywhere, converted only inside a backend.
- **New gate**: add to `core/guardrails/gates.py` with a stable issue `code`, classify it in `core/guardrails/policy.py`, a negative test in `tests/`, and mention it in `benchmarks/SPEC.md` if it is a G-gate.

## Rules that keep it maintainable
1. One reason to change per module; if a file needs a backend name, it is in the wrong layer.
2. No module-level mutable configuration shared across calls (backends hold style on the instance).
3. Every behaviour has a falsifying test; every negative claim in docs is backed by an `evidence/` file.
4. Gates always measure with the local backend, even when exporting with another one (documented approximation).
5. The top-level folder list is closed (`tests/test_architecture.py::TOP_LEVEL_ALLOWED`); a new folder needs a line in `architecture/ARCHITECTURE_MAP.md`.

## Harness guardrails (ADR-0009)
Blocking vs advisory gates (`core/guardrails/policy.py`), immutable `attempts/NN/` + `ledger.jsonl` per out dir, fresh-review binding in `engine/review.py` (`review-context` -> independent reviewer -> `record-review` -> `finalize`). The engine never scores taste; it only binds what was reviewed.

## Known debt
- Scene v0.2 `element.style` (font/color/align/line_height/fill) is rendered by `backends/local` only; DesignCraft ignores it and reports that in its export notes.
- `cases/approved/` is empty: every run is tagged `NO_EXTERNAL_REFERENCE` (core/references.py, cases/RIGHTS_PROTOCOL.md). B1 "cases" currently retrieves synthetic patterns, not real cases.
- `backends/local` and DesignCraft compose text differently, so gate text-fit is approximate for DesignCraft output.
- `core/guardrails/gates.py` loads `scripts/check_layout.py` / `check_edit_diff.py` by path (single implementation shared with the CLI scripts); migrating them into `core` would remove that coupling.
- `authors/rule_based` = editorial rules (`plan.py`) + pagination/hero search; it owns no geometry any more (that is `layout/`).
- Style tokens (`spec["style"]`) are an untyped dict; a schema is not written yet.
