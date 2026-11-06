# Adapters — compare, do not blindly combine

Each candidate needs capability discovery and a narrow contract:
`capabilities()`, `create(book_plan,assets,design_profile)`, `edit(revision,scoped_patch)`, `render(revision)`, `export(revision,format)`, `inspect(revision)`.

The present repository contains **specifications only**, no working design backend adapter or active MCP server. Do not claim automatic PDF generation until P04/P06 demonstrably implemented.

- `openpencil/` — preferred first editor spike, not selected.
- `genoffice/` — independent editable office/PDF spike, not selected.
- `diagram-design/` — optional SVG diagrams; no CAD/BIM accurate geometry assumption.
- `harnessrouter/` — optional external harness executor/benchmark, not plugin requirement.
- `pdf-source/` — fallback PDF content embedding to preserve vectors only if proven.
