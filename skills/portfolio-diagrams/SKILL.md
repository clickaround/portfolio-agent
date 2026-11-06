---
name: portfolio-diagrams
description: Make the conceptual diagrams a portfolio needs (massing steps, site, circulation, process strips) as editable SVG, in the book's colours, and hand them to the portfolio engine. Use when a project has a Concept/Process section but no diagrams, or when the user asks for diagrams.
---

# Portfolio diagrams

Two producers, same delivery contract (`diagram-set/v1`, from the user's DiagramAgent in `agents/pascal-agents/DiagramAgent/contracts/diagram-set.schema.json`):

1. **diagram-design** (MIT, cathrynlavery/diagram-design commit f24d98b; verbatim copy with LICENSE at `skills/diagram-design/` in this plugin and in `agents/pascal-agents/DiagramAgent/skills/diagram-design/`; run it with `claude -p` giving the SKILL.md path, the book tokens and project.md; export with `python skills/diagram-design/scripts/export_svg.py <html>`). Never draw diagrams by hand as SVG primitives (2026-11-05: hand-drawn ones were judged "placeholder-looking" by the blind critic). 45 editorial diagram types as self-contained HTML + inline SVG; its style guide takes the book's tokens (paper / ink / accent). Use for concept, process, flow, timeline, quadrant and chart diagrams. Export the SVG (`/export-diagram <file> --svg-only`, or write the SVG directly).
2. **DiagramAgent** (the user's own, `agents/pascal-agents/DiagramAgent`): overlay diagrams on real site plans / drawings (arrows snapped off buildings, labels placed by cost), massing, zoning, circulation; needs its engine venv and the Claude Code CLI. Use for architecture reports where the diagram must sit on a real drawing.

## Rules (both producers)
- Facts only from `project.md` and the placed drawings; a diagram illustrates the text, it never adds dimensions, areas or claims. Label conceptual diagrams as such.
- Colours = the book's tokens (`tokens` in the book plan, `--design-md` palette, or defaults ink `#1B1B1B` / accent `#B44A2B`); flat, no shadows, one accent, text >= 12 px at 600 x 420.
- Deliver into `<project>/diagrams/diagram_NN.svg` plus `diagrams/diagram-set.json` (`contract_version`, `project`, `diagrams[{id, type, title, caption, svg, png, width_px, height_px, plan, sha256}]`; fill `sha256` of each SVG). The engine ingests them as role `diagram`, puts 2-4 on one row (`diagram_row`) with the titles as captions, and keeps them vector in the PDF (and in DesignCraft).
- Then run `compose` / `run` as usual; check the preview of the Process page before finishing.
