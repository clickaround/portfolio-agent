# Contributing

Read `project/AGENTS.md` (mission, evidence labels, licence gate), the workspace `README.md` (map), then the `AGENTS.md` of the agent you touch. Speak Korean with the owner; code, contracts and commit messages are English.

## Run
```
cd agents/portfolio-plugin
python scripts/portfolio.py compose <project> <book-plan.json> <out> --width-mm 297 --height-mm 210 --bleed-mm 3
python -m pytest ../../backend/common/tests ../portfolioAgent/tests ../sourcePrepAgent/tests ../reviewAgent/tests -q      # ~6 min; fast: backend/common/tests + portfolioAgent/tests/test_photoset.py
cd ../../project && python -m pytest tests -q && python scripts/validate_package.py
```
Fixtures: `agents/portfolioAgent/examples/synthetic_projects/*` (synthetic). Real sources stay outside the repo.

## Rules
1. **One agent = one folder** (`agents/<name>Agent/`: `AGENTS.md`, `src/`, `tests/`). A new capability goes to the agent that owns the responsibility, or becomes a new agent folder; never a patch spread over several.
2. **Layers** (enforced by `backend/common/tests/test_architecture.py`): `core (backend/common) <- layout <- authors/*, backends/* <- engine <- cli`. `sourcePrepAgent` and `reviewAgent` import `core` only. `portfolio_agent` and `portfolio_agent.engine` are PEP 420 namespaces: never add an `__init__.py` there.
3. **Shared code lives in `backend/common`** and is changed with every agent's tests green. Agent-specific code never goes there.
4. **Variety is data, not code**: grid systems, compositions, photo sets are JSON in `portfolioAgent/knowledge/patterns/`; tests check cells never overlap.
5. **The host LLM decides editorial things, rules execute**: the book plan (`backend/common/contracts/book-plan.schema.json`) carries roles, assets, words, flags; never coordinates.
6. **Guardrails**: new check = a code in `core/guardrails/policy.py` (BLOCKING or ADVISORY) + the check in `gates.py` + a falsifying test.
7. **Provenance**: source bytes are never modified; every transform keeps the original in `sources/` and a record in `derived.json`.
8. **Reuse before writing**: MIT/Apache may be copied with attribution; AGPL/GPL/no-licence read-only. Every reuse goes in `project/research/REUSE_MAP_*.md` as "from -> to". Third-party binaries live in `.cache/bin` (ignored), verified by SHA256SUMS + signature.
9. **Evidence, not claims**: a quality change ships with the contact sheet you looked at; scored runs write `reviewAgent/benchmarks/reports/<run>.json` (blind, key in `.cache/_unblind_key*.json`). One LLM critic is noise +-0.07; only human blind pairwise review counts as quality evidence.
10. **Privacy**: no third-party portfolio PDFs, no real client sources, no secrets in the repo (`.gitignore` blocks the usual paths). No Anthropic API billing: LLM calls go through the Claude Code / Codex CLI.

## Ownership (proposed; edit when the team forms)
| area | paths |
|---|---|
| Layout engine | `agents/portfolioAgent/src/portfolio_agent/layout`, `.../knowledge/patterns` |
| Guardrails + shared core | `backend/common` |
| Source preparation | `agents/sourcePrepAgent` |
| Review + benchmarks | `agents/reviewAgent` |
| Skills (host-facing) | `agents/portfolio-plugin/skills/portfolio-*` (`skills/diagram-design` is a verbatim MIT copy: re-copy, do not edit) |
| Backends (exporters) | `agents/portfolioAgent/backends` |
| Diagrams, decks | `agents/pascal-agents/*` (own repo; coordinate with its owners) |
| Governance, research | `project/` |

## Before a PR
All three test commands green, `project/scripts/validate_package.py` ok, the sheet you looked at attached, one line in `project/memory/NOW.md`.
