# ArchPortfolioBench v0.1 — benchmark FIRST

**Type:** proposal/protocol, not yet executed. Evaluate *designs used by professionals* rather than model-generated pictures alone. Separate test dimensions; a great aesthetic cannot redeem a corrupted drawing.

## Prior art; do not conflate
- [GDB GraphicDesignBench](https://github.com/lica-world/GDB): graphic layout, typography, SVG, template tasks, code pipelines. Authors' benchmark numbers are NOT our portfolio results.
- [SlidesGen-Bench](https://github.com/YunqiaoYang/SlidesGen-Bench): content fidelity / aesthetics / editability (PEI levels) and human alignment. Slide aesthetics may disagree with minimal architecture layouts.
- [AutoDesign PosterBench](https://github.com/Yaxin9Luo/AutoDesign/tree/main/eval): source-conditioned faithfulness/coverage/density/visual evidence/layout/readability/aesthetics. Academic poster distribution, not architecture.
- [DECKBench](https://github.com/morgan-heisler/DeckBench): multi-turn slide edits and deck coherence; similarity to reference need not equal novel design quality.
- [Paper2Poster](https://github.com/Paper2Poster/Paper2Poster): source factual QA; useful for information conveyance and no-hallucination tests.

## Six independent axes
**HARD GATES (blocking):**
- `G1`: referenced assets exist, source SHA intact; user-uploaded bytes never changed.
- `G2`: drawings retain permitted original crop/scale, relevant text/line weights; sample human zoom review.
- `G3`: no unintentional clipping or page overflow, font substitution critical defects, illegal overlap.
- `G4`: claims/measurements and contributions source-linked; no invented facts.
- `G5`: recipient AI-use policy and page/file size constraints checked; if unknown, warn/block submission claim.

**SCORES (never override gates):**
- `C`: content selection/coverage/traceability — human + source-conditioned QA.
- `L`: composition, hierarchy, whitespace, layout quality — deterministic geometry + expert ratings.
- `E`: editability + localized-edit stability — native-object count and diff.
- `D`: domain fit and reader understanding — architecture criteria, domain expert.
- `N`: multipage story and design rhythm — sequence + human comprehension.
- `O`: operational cost, latency, failure/retry/time to finish.

## Tasks: validate both creation and editing
| ID | Stimulus | Expected measurable behavior |
|---|---|---|
| AP-01 | classify plan, section, rendering, diagram | exact label vs human-reviewed label; unknown stays unknown |
| AP-02 | use user sources, no invented role/measure | provenance and source truth QA |
| AP-03 | A3 landscape 2-page book | page-size, clipping, source preservation |
| AP-04 | same references, 3 visual candidates | nontrivial layout differences + human blind choice |
| AP-05 | 20% enlarge one drawing | target change, allowed reflow only, others stable |
| AP-06 | double caption length | overflow must trigger repair or controlled text reflow |
| AP-07 | revise page 2 only | unaffected page 1 hash/state unchanged |
| AP-08 | export PDF & editable artifact | open files, object editability, preview parity |
| AP-09 | case-conditioned vs case-free | same input/model/cost and pairwise preference |
| AP-10 | Claude/Codex different host | identical task protocol + trace logs; no forced equal model quality |

## Split & fairness
- Source projects/creators are disjoint across `reference`, `development`, `heldout`.
- P01 begins with a few licensed full portfolios; benchmark heldout set grows independently. Minimum sample targets are estimates, not statistically certified.
- Match page dimension, content inputs, model ID, tools, retry budget, reference count, and cost/time where possible. Log differences.
- Record run IDs, source hashes, backend SHA/version, prompt version, render dpi, browser/PDF engine, model/Judge ID, API cost, timestamp.
- Use at least 2 independent expert reviewers; randomized unlabeled pairwise comparison, allow tie/invalid. Record reasons and disagreement. No tuning on heldout decisions.
- Do not solely optimize a VLM rating or colorfulness score; expert preference is the human-relevant measure.

## Proposed gate for first PoC
0 catastrophic source alterations, 0 critical clips, 0 fabricated facts; layout patch limited; 2-page book and 3 candidate generation with evidence; uncorrected output labeled FAILED. Quality improvement over B0 measured, not asserted. Export/fidelity failures can be reported and still count as a useful spike, but not a release pass.
