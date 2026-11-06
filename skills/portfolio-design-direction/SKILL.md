---
name: portfolio-design-direction
description: Act as DesignDirector for a portfolio - write a project-specific design plan (palette, type, grid, layout concept, principles), check it against generic-template defaults, then drive the engine with it and critique the result.
---
# Portfolio Design Direction

Process adapted from Anthropic's `frontend-design` skill (Apache-2.0, https://github.com/anthropics/claude-plugins-official, pinned in `research/repos.lock.json` as `anthropic-plugins`) and re-targeted to multi-page portfolios in print/digital formats. Output tokens and composition constraints, never pixel coordinates.

## 1. Ground the brief
Identify the domain (architecture, UX, graphic/branding, photography, industrial, illustration, research...), the reader (admissions, client, jury, recruiter), the medium and page size, and what the strongest 1-3 projects are. Read `knowledge/domains/<domain>.md` and `knowledge/editorial/grammar.md`. Facts and images come only from the asset manifest.

## 2. Write `design-plan.json` (compact)
```json
{
  "palette": {"paper": "#ffffff", "ink": "#1a1a1a", "accent": "#...", "muted": "#..."},
  "type": {"title_font": "<font file or installed name>", "body_font": "<...>", "title_scale": 1.0, "body_pt": 11},
  "grid": {"margin_mm": 14, "gutter_mm": 6},
  "layout_concept": "one sentence + optional ASCII wireframe per page role",
  "footer": false,
  "principles": ["spend boldness in one place", "..."],
  "generic_defaults_checked": ["cream+serif+terracotta", "identical cards", "all-caps eyebrow labels", "numbered markers without a real sequence", "tracked-out labels"]
}
```
Palette 4-6 named hexes; user's own brand/colour request always wins. White background is the default unless the brief says otherwise.

## 3. Review the plan before building
Ask: would I produce this same plan for any other portfolio in this domain? If a part is a generic default, change it and state what and why. Do not accent a single headline word, do not add numbered markers unless the content is a sequence, no decoration that does not carry information.

## 4. Build, then critique
`python scripts/portfolio.py candidates <project> <out> --design-plan design-plan.json` (>= 3 distinct candidates). Gates first (`qa.json`), then an INDEPENDENT critic using `knowledge/editorial/critic-rubric.md`. Apply the critic's issues via `local_refine` / `pivot_layout` / `revise_story`. A gate failure or critic `fail` is reported as such, never as finished.

## 5. Limits
A plan the host writes is a hypothesis; design quality is only claimed after blinded domain-expert pairwise review (`benchmarks/HUMAN_REVIEW.md`).
