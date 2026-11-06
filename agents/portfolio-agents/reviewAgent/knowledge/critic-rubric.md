# Independent visual critic rubric (portfolio pages)

Structure adapted from AutoDesign `prompts/critic_vision_poster.md` (MIT, (c) AutoDesign authors): dimension scores, severity levels, repair routes, "do not invent issues". Re-written for multi-domain portfolios.

**Independence rule:** the critic must be a fresh agent or person that did NOT generate the candidates. It sees only candidate PNG sheets, `review_context.json` (domain, purpose, page sizes, asset roles, deterministic gate results) and this rubric. It must not see which engine settings produced which candidate (`_unblind_key.json` is off limits).

## Score 0-1 per dimension (cite page + evidence for any score below 0.6)
1. `hierarchy` — one clear hero per page, readable reading path, title > heading > body > caption.
2. `composition_balance` — visual weight distribution, alignment to a consistent grid, no orphaned blank areas that look accidental.
3. `whitespace_intent` — empty space reads as deliberate (margins, breathing room), not leftover from fitting.
4. `typography` — scale contrast, line length, leading, no tiny text, consistent family.
5. `sequence_narrative` — page order tells the project story; rhythm varies (cover / overview / hero / detail / close); no repeated identical layouts.
6. `asset_fidelity` — nothing stretched, cropped or recolored; drawings legible at page size; source labels intact.
7. `domain_fit` — conventions of the domain (architecture: drawings large, crisp linework; photography: image-led, minimal text; UX: flow/screens + rationale; branding: system consistency; product: process + final).
8. `anti_template` — does not look like a generic auto-generated report.

## Issues
Each issue: `page`, `severity` (blocker | high | medium | low), `category` (a dimension above), `description` (<= 200 chars), `evidence`, `suggested_route` = `local_refine` (same layout, tweak) | `pivot_layout` (different composition) | `revise_story` (page order / selection) | `revise_type_system` | `none`.

Verdict: `pass` (mean >= 0.75, no blocker/high) | `revise` | `fail`. Rank candidates, or pick none if all fail. A deterministic-gate failure is never overridden by a critic.

## Limits
A single LLM critic is not a designer. Claims of design quality require domain-expert blinded pairwise review (`benchmarks/HUMAN_REVIEW.md`).
