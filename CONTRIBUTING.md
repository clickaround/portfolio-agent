# Contributing to portfolio-agent

Read `AGENTS.md` (mission, evidence labels, licence gate), then `docs/STRUCTURE.md` (where things live). Speak Korean with the owner; code, contracts and commit messages are English.

## Run it
```
set PYTHONUTF8=1
python scripts/portfolio.py compose <project> <book-plan.json> <out> --width-mm 297 --height-mm 210 --bleed-mm 3
python -m pytest tests -q          # ~6 min; fast subset: tests/test_bleed.py tests/test_photoset.py tests/test_architecture.py
```
Fixtures: `examples/synthetic_projects/*` (synthetic, labelled). Real sources stay outside the repo (see workspace `README.md`).

## Rules that keep a shared codebase maintainable
1. **Layers** (enforced by `tests/test_architecture.py`): `core(+guardrails) <- layout <- authors/*, backends/* <- engine <- cli`. A lower layer never imports a higher one; backends import only `core`.
2. **One capability = one module in its layer**, with its own test file: `layout/bleed.py` + `tests/test_bleed.py`, `layout/photoset.py` + `tests/test_photoset.py`, `engine/cutout.py`, `engine/levels.py`. No patches spread over five files.
3. **Variety is data, not code**: grid systems, compositions, photo-set templates are JSON in `knowledge/patterns/`. A new arrangement = one entry; tests check cells never overlap.
4. **The host LLM decides editorial things, rules execute**: the book plan (`contracts/book-plan.schema.json`) carries roles, assets, words, flags (`bleed`, `dark`, `strip`, `photoset`, `focus`). It never carries coordinates. Do not add coordinate fields.
5. **Guardrails**: new check = a code in `core/guardrails/policy.py` (BLOCKING or ADVISORY) + the check in `gates.py` + a test that falsifies it. Unknown codes fail closed.
6. **Provenance**: source bytes are never modified. Any transform (trim, levels, knockout, cut-out) keeps the original in `sources/` and is logged in `derived.json`.
7. **Reuse before writing**: MIT/Apache code may be copied with attribution; AGPL/GPL/no-licence is read-only. Every reuse goes into `research/REUSE_MAP_*.md` as "from -> to". Third-party binaries live in `.cache/bin` (ignored), verified by SHA256SUMS + signature.
8. **Evidence, not claims**: a quality change ships with the contact sheet you looked at and, if scored, a `benchmarks/reports/<run>.json` (blind, key kept in `.cache/_unblind_key*.json`). One LLM critic is noise ±0.07; only human blind pairwise review (`benchmarks/HUMAN_REVIEW.md`) counts as quality evidence.
9. **Privacy**: no third-party portfolio PDFs, no real client sources, no secrets in the repo. `.gitignore` blocks the usual paths; if in doubt, keep it outside the repo.
10. **No Anthropic API billing**: LLM calls go through the Claude Code / Codex CLI on a subscription (inherited from pascal-agents).

## Ownership (proposed; edit when the team forms)
| area | paths |
|---|---|
| Layout engine | `runtime/portfolio_agent/layout/`, `knowledge/patterns/` |
| Guardrails + harness | `runtime/portfolio_agent/core/guardrails/`, `engine/review.py`, `architecture/adr/0009-*` |
| Source preparation | `engine/prepare.py`, `levels.py`, `cutout.py`, `assets.py` |
| Skills (host-facing) | `skills/portfolio-*` (`skills/diagram-design` is a verbatim MIT copy: do not edit, update by re-copying) |
| Backends | `backends/{local,designcraft}` |
| Research + benchmarks | `research/`, `benchmarks/`, `evidence/` |
| Agents integration | `agents/pascal-agents/*` (separate repo; coordinate with its owners) |

## Before you open a PR
`python -m pytest tests -q` green, `python scripts/validate_package.py` ok, the sheet you looked at attached, `memory/NOW.md` one line updated.
