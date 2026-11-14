# portfolioAgent Tool Guidance

<!-- Harness² C4 tool guidance (tool_descriptions/tool_guidance.md). Every call. When and how to use each existing tool. -->

- Order: `manifest` (what the project has) -> `grid` or `catalogue` (what the page can hold) -> write `book-plan.json` -> `compose` -> look at `preview` -> `edit-element` for a local change.
- `compose` is the normal path. `run` is the rule-only pipeline for benchmark conditions.
- `edit-element` (CLI command `edit`) changes one element's text on one page and records the result as the next attempt. Do not recompose a whole book for a local change. A review made before the edit no longer applies.
- `check-scenes` gates scenes that came from elsewhere. `candidates` (several options for the same project) is a CLI command without a declared tool; run it through the shell.
- Pass the design direction with `--design-plan` or `--design-md`; do not hard-code colours in the plan.
