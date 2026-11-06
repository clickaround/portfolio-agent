# Repository structure (2026-11-05, for collaborators)

```
portfolio-agent/
  README.md AGENTS.md CLAUDE.md CONTRIBUTING.md GOALS.md PLANS.md       entry + rules
  .claude-plugin/ .codex-plugin/ .agents/                                host plugin manifests
  skills/            host-facing workflows (portfolio-create, -design-direction, -diagrams, -cutout, ...; diagram-design = MIT copy)
  runtime/portfolio_agent/                                               the engine (Python)
      core/ (+guardrails/)   contracts, assets, geometry, gates, grounding, page metrics   [lowest layer]
      layout/                typesystem, compositions, bleed, photoset, modular, treelayout, book
      authors/               rule_based (baseline), planned (host book plan), host (scene JSON, legacy B4)
      engine/                pipeline, prepare, levels, cutout, review, catalogue, grid, spec, registry
      cli.py                 only parses arguments and calls engine
  backends/{local,designcraft}/   exporters/measurers behind an adapter contract
  contracts/         JSON schemas (book-plan, scene-document, ...)
  knowledge/         DATA: patterns/ (grid systems, compositions, photosets), editorial/ (craft rules, critic rubric), domains/, cases/ (annotations only)
  benchmarks/        SPEC + protocol + reports/<run>.json (blind runs)
  evidence/          what was run and seen (md + logs/); big binaries do not belong here
  research/          pinned repos (repos.lock.json), paper notes, REUSE_MAP
  architecture/      ARCHITECTURE_MAP, ADRs
  tests/ examples/   tests + synthetic fixtures (the only inputs a teammate needs)
  scripts/           thin entry points (portfolio.py, contact_sheet.py, guides_overlay.py, validate_package.py ...)
  agents/ tasks/ plans/ prompts/ cases/ formats/ integrations/ docs/ memory/   design package (task DAG, roles, protocols, NOW.md handoff)
  .cache/ preview/ .remember/ .pytest_cache/   local/generated, ignored
```

Where does a new thing go?
| I want to add... | put it in | also |
|---|---|---|
| a page arrangement | `knowledge/patterns/*.json` | `catalogue` sheet + test |
| a new page device (like bleed) | `layout/<device>.py` | gate rule if it breaks a constraint, schema field, skill paragraph, test |
| a source transform | `engine/<transform>.py` | `derived.json` record, CLI flag, test that the original is untouched |
| a check | `core/guardrails/` | policy code + falsifying test |
| a diagram producer | `agents/pascal-agents/DiagramAgent` | `diagram-set/v1` output |
| an export format | `backends/<name>/adapter.py` | capability declaration |

Known debt (not fixed on purpose, to keep paths stable while the team forms): root clutter `README_START_HERE.md`, `VALIDATION_REPORT_V2/V3.md` (referenced by `scripts/validate_package.py`); `core/` at the root is docs only (code is `runtime/portfolio_agent/core`); `cases/` vs `knowledge/cases/`; evidence logs are large. Folder rename `portfolio-agent` -> keep: it equals the plugin id.
