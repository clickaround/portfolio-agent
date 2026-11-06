# portfolio-plugin - the Portfolio plugin shell (Claude Code / Codex)

Plugin root only: `.claude-plugin/`, `.codex-plugin/`, `.agents/plugins/marketplace.json`, `plugin.json`, `skills/` (host-facing workflows; each names the agent that owns it), `scripts/portfolio.py` (single CLI entry). No engine code lives here.

Mission, evidence labels, licence gate: `../../project/AGENTS.md` (read first). Speak Korean with the owner; code and contracts in English.

## The agents (one folder each, siblings of `../pascal-agents`)
| agent | owns | in -> out |
|---|---|---|
| `../sourcePrepAgent/` | trim scanned sheets, levels/knockout, cut-outs (rembg, photocraft), original-preserving `derived.json` | raw project folder -> `images/ drawings/ diagrams/ sources/ derived.json` |
| `../portfolioAgent/` | the book: host-LLM book plan -> grid/bleed/photo-set layout -> guardrails -> PDF/PPTX/PNG | `book-plan.json` + manifest -> `book.pdf`, `scenes/`, `qa.json`, `attempts/NN` |
| `../reviewAgent/` | fresh-review gate, critic rubric, blind runs, benchmarks | PNG frames + hashes -> `review.json`, `benchmarks/reports/*.json` |
| `../pascal-agents/DiagramAgent` | diagrams: concept (diagram-design) + overlays on real drawings | `diagram-set/v1` |
| `../pascal-agents/pptAgent` | deck design system, palettes | `DESIGN.md`, `layout/v1` |

Shared code: `../../backend/common` (`portfolio_agent.core`, JSON `contracts/`). HTTP API over the agents: `../../backend/api`.

## Run (from this folder)
```
python scripts/portfolio.py prepare|cutout <project> ...        # sourcePrepAgent
python scripts/portfolio.py compose <project> <book-plan.json> <out> --width-mm 297 --height-mm 210 --bleed-mm 3   # portfolioAgent
python scripts/portfolio.py review-context|record-review|finalize <out> ...      # reviewAgent
python -m pytest ../../backend/common/tests ../portfolioAgent/tests ../sourcePrepAgent/tests ../reviewAgent/tests -q
```
Import name stays `portfolio_agent` (PEP 420 namespace over the agents' `src/` roots; `backend/common/src/pascal_bootstrap.py` sets `sys.path`). Never add `__init__.py` to `portfolio_agent/` or `portfolio_agent/engine/`.
