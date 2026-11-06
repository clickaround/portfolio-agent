> **ARCHIVED V2 CONTEXT — non-authoritative.** Current: `AGENTS.md`, `GOALS.md`, `PLANS.md`, `architecture/ARCHITECTURE_MAP.md`, `research/repos.lock.json`, `formats/`.

# Repository decision matrix — **candidate** not dependency list

| Component | Repo | Actual capability to verify | Integration stance | Main risk |
|---|---|---|---|---|
| Agent execution | HarnessRouter/harnessrouter | UHP responses-compatible tasks, sessions, files, conformance | **Optional P08** | own Docker+keys, duplicated orchestration in direct plugin use |
| Editable canvas | open-pencil/open-pencil | CLI/MCP operations, SVG/PDF/PPTX export, design lint | **P04 candidate A** | source PDF import, linework, fonts, performance |
| Office slides/PDF | genspark-ai/genoffice | CLI/MCP `deck_page`, `slides_audit`, native PPTX | **P04 candidate B** | document vs A3 editorial constraints, PDF vector fidelity |
| Diagram grammar | cathrynlavery/diagram-design | SVG HTML diagram types and structural checks | **optional adapter P06** | not architectural geometry from CAD, fixed aesthetic |
| Design/review workflow | Yaxin9Luo/AutoDesign | browser HTML poster generation/review/repair | **baseline P02** | research-paper rather than architecture source, dependencies |
| Global deck plan | sxswz213/DeepSlides | design-before-code, ablation switches | **study/reference P02** | complex stack / trained model claims not equivalent to untrained pipeline |
| Content poster | Paper2Poster/Paper2Poster | paper-to-poster and QA | **baseline P02** | paper-centric inputs, bundled dependency/licensing scope |
| Editable HTML runtime | archlizheng/frontend-slides-editable | drag resize editable HTML decks | **alternative P04** | not exact PDF source preservation |
| Fixed poster | yejy53/Editable-Design | layered HTML fixed canvas + replay | **techniques only** | skill explicitly rejects slide decks, cannot simply productize multi-page |
| HTML→PPTX | Hasasasa/html-to-editable-pptx | separate native text/shape from CSS raster decor | **optional export** | fidelity / locale fonts |
| Layout constraints | google/or-tools | deterministic geometry/constraint solving | **optional if experiment demonstrates need** | overengineering/fixed grammar |
| Graphic eval | lica-world/GDB | layout, SVG, typography, graphics | **evaluation adapter** | dataset availability and metric assumptions |
| Slide eval | YunqiaoYang/SlidesGen-Bench | content/aesthetics/editability | **evaluation methods** | slides vs architecture pages; score calibration |
| Multi-turn eval | morgan-heisler/DeckBench | deck coherence and multi-round edits | **evaluation methods** | reference matching may punish novelty |

## Gating rule
Read the exact commit specified in `repos.lock.json`. For each candidate run a self-contained **minimal smoke test** and save: setup commands, runtime/env, API key requirements (never values), sample input, produced output + checksum, test logs, license of transitive assets. Until then status stays `METADATA_VERIFIED` / `NOT_RUN`.

## Backend comparison (no winner assumed)
| Criterion | OpenPencil | GenOffice | Local SVG/PDF fallback |
|---|---|---|---|
| Editable vector/text | README claim | README claim | only if implemented |
| PDF drawing vector preserved | UNKNOWN | UNKNOWN | requires PDF embed spike |
| A3 page/export parity | UNKNOWN | UNKNOWN | page-size possible, must test |
| Host integration | CLI/MCP documented | CLI/MCP documented | local scripts |
| Commercial use | verify MIT dependencies | verify Apache/third parties | our code + PDF library licenses |
| Time to prototype | low setup risk? **unverified** | low setup risk? **unverified** | larger build effort |

## Reproduction outcome labels
`NOT_RUN` → `SETUP_BLOCKED` / `SMOKE_PASSED` / `SMOKE_FAILED` → `PORTFOLIO_INPUT_PASSED` / `PORTFOLIO_INPUT_FAILED`. Never collapse these into a vague "supported".
