# Notes: AI Harness Engineering (arXiv 2605.13357) and DeepSlides (ACL 2026 Findings) — 2026-11-05

Labels: DOC_REPORTED (2605.13357: abstract + metadata only, full text not fetched yet) · DOC_REPORTED + CODE_INSPECTED (DeepSlides: README, `src/open_deep_research/graph.py|prompts.py` structure; clone `.cache/vendor/deepslides`, MIT).

## 1. AI Harness Engineering — "a runtime substrate between the model and the project"
Claim: software-engineering capability emerges from the **model-harness-environment system**, not the model. Eleven harness responsibilities are named; a four-level ladder **H0-H3** progressively exposes runtime support; a trace-based protocol turns each run into an **auditable episode package**; one controlled task shows that higher levels add "reproduction logs, failure attributions, deterministic requirement checks, and structured verification reports" (no quantitative benchmark in the abstract).

Mapping of the eleven responsibilities to Portfolio Agent today (what exists / what is missing):
| responsibility | ours | gap |
|---|---|---|
| task specification | book-plan schema + skill text | fine |
| context selection | `manifest`, `grid`, `catalogue`, previews | fine |
| tool access | host allow-list (`Bash(python scripts/portfolio.py:*)`) | Codex has no Read tool → shell reads allowed (fixed) |
| project memory | `attempts/NN` + `ledger.jsonl`, `memory/NOW.md` | no cross-run recall of what worked per domain |
| task state | `qa.json` per attempt | fine |
| observability | ledger, review-context hashes, host JSON result (cost, turns) | no unified episode package per run |
| failure attribution | issue codes bound to element ids + pages | fine |
| verification | blocking gates + fresh review | fine |
| permissions | host permission mode; rights gate for cases | fine |
| entropy auditing | — | **missing**: nothing measures drift across attempts (e.g. plan churn, repeated advisories) |
| intervention recording | `record-review` stores reviewer mode; human edits not logged | **missing**: no record of the person's manual changes |
Decision: produce an **episode package** per run (`attempts/NN/episode.json`: plan sha, host, model, cost, gate/advisory history, review, interventions) — cheap, and it is what UHP/HarnessRouter would consume as the task result. Matches ADR-0009; extends it with entropy (advisory churn) and intervention fields.

## 2. DeepSlides — "Design First, Code Later"
Two levels: **slides-level design** (global identity: tone, palette, decorative shapes, layout-diversity rules; functional pages typed) and **page-level generation** in four stages: content expansion → **design in three layers (background / layout / content)** → implementation (python-pptx code) → evaluation on **completeness, compliance, aesthetics** with iterative refinement of low scores. Designer and coder are separate roles so a design error does not become a code error. Self-reported: 76.5 % top-1 human preference vs open-source baselines, 52 % vs commercial.
What it means for us:
- Our book plan = slides-level design; our compositions = the layout layer; our tokens = palette. **We have no background layer** (bands, spines, decorative shapes) — exactly what the critic rewarded in B0 (brick-red spine, warm ground). Add a declarative background layer to the book plan (`background: {band: left|top|none, colour, width_mm}`) rendered as locked shapes under the grid.
- Their per-page evaluate→refine on three named scores is our advisory diagnostics + fresh review, but ours is book-level only. Add page-level scores in `qa.json` (completeness = required slots filled, compliance = gates, aesthetics = diagnostics) so the host can target the weakest page.
- Designer/coder split = our host (plan) / layout layer (code). Confirms the architecture decided on 2026-11-05.

## Not read yet
2605.13357 full text (the exact definitions of "entropy auditing" and the H0-H3 ladder); DeepSlides paper PDF beyond the README; the ReDeck / PosterVisor threshold papers that `agents/pascal-agents` already extracted (reuse their notes instead of re-reading).

## 3. Agentic Harness Engineering, AHE — NOT Google's Harness² (that is arXiv 2610.14224; see `../architecture/AGENT_FOLDER_STANDARD.md`). Earlier mislabelled "Harness 2": (arXiv 2604.25850, v2 29 Apr 2026, v4 18 May 2026) — DOC_REPORTED (abstract page)
Automates harness-level evolution by instrumenting the three stages of an engineering loop (component editing, trajectory inspection, decision making) with three observabilities: **component** (each editable harness component is a file, edits explicit and revertible), **experience** (raw trajectories distilled into a layered evidence corpus), **decision** (every edit carries a self-declared prediction checked against the next round's task outcomes). Terminal-Bench 2 pass@1 69.7 -> 77.0 % in ten iterations (above the human-designed Codex-CLI harness 71.9 %); SWE-bench-verified top aggregate at 12 % fewer tokens; +5.1 to +10.1 pp transfer across model families (self-reported).
For us: component observability already holds (skills, compositions, grid systems, tokens, rubric are all files); experience observability = the new `attempts/NN/episode.json` + ledger; **decision observability is missing**: every rule/skill change I make should carry a one-line prediction ("heading 3 steps above body -> critic 'hierarchy' >= 0.7") that the next blind round checks. Adopted as a process rule in evidence files from now on (see evidence/LAYOUT_V2_AND_HARNESS_2026-11-05.md, "Predictions").
