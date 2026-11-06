# Paper audit — what to read and why

> This is a research plan with code-inspected hints; do not say full appendices were reviewed. Every paper entry gets a new `research/paper-reviews/<slug>.md` with figure/table IDs and page citations after P02.

| Work | Hypothesis of reusable contribution | Important implementation inspected | Metrics/claim trap | Required falsification |
|---|---|---|---|---|
| GraphicDesignBench (2026) | task-oriented layout/SVG/typography benchmark | `src/gdb/tasks/layout.py`, `metrics/core.py` | 49 paper tasks vs 40 public pipelines: not interchangeable | `gdb verify`; one task on local fixture; record dataset license |
| SlidesGen-Bench (2026) | content, visual aesthetics, editability must be separated | `eval/aesthetics_metrics.py` + quiz accuracy | slide aesthetics != architecture portfolio quality | rerun aesthetic metric on 10 minimal reference pages and compare human ratings |
| AutoDesign (2026) | design harness improves fixed model without fine-tuning | `agent_skills/autodesign-poster` and PosterBench evaluator | PosterBench academic posters, not architecture; human correlation limited | run identical assets under zero vs review/repair budget |
| DeepSlides (2026) | global design planning improves page consistency | LangGraph `src/open_deep_research/graph.py`, ablate flags | claims may include trained SlideQwens, not reproducible with only prompts | run with and without design plan using same model/budget |
| Paper2Poster (2025) | source evidence + visual story / QA | `Paper2Poster-eval/eval_poster_pipeline.py` | paper semantic QA not architectural source integrity | transform synthetic architecture brief, test no invented facts |
| DECKBench (2026) | multi-turn deck editing reliability | `metrics/deck_metrics.py` | reference similarity can penalize legitimate design variety | edit 1 object and check unchanged-elements diff |
| Editable-Design (2026) | fixed-canvas editability and replay | `skills/editable-design/SKILL.md` | poster skill explicitly excludes slide decks | one page run only; no unjustified multi-page extrapolation |
| Diagram Design (2026) | explicit design grammar and SVG checks | `skills/diagram-design/SKILL.md`, `scripts/self_check.py` | 45 illustrative diagrams != CAD/BIM accurate drawings | test semantic layout fidelity + exported SVG geometry |

## Full-read template (one per paper)
1. Full bibliographic record / version / source URL / pages reviewed.
2. Task definition, domain, input/output, architecture diagram from paper.
3. Formulae and objective functions with named variables.
4. Training data size/source/access/license, train/dev/test split, contamination risks.
5. Model sizes/checkpoints/downloads, compute and inference budget.
6. Baselines, exact metrics, confidence, ablations, human study, failures and null results.
7. Code–paper correspondence: paths, gaps, mismatch, tests, commit SHA.
8. Reproduction commands, actual log paths, environment, expected vs observed.
9. Transfer test to portfolio, negative transfer risk, decision: reuse/reference/reject.
