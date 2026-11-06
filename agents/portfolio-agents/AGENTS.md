# portfolio-agents — the Portfolio plugin (Claude Code / Codex)

People put in their sources (photos, drawings, diagrams, brief); these agents arrange and beautify them into a professional portfolio. Hub of three sub-agents (like `../pascal-agents`), one folder each, each with identity (`AGENTS.md`), tests and a contract. Mission, evidence labels, licence gate: `../../project/AGENTS.md` (read it first). Speak Korean with the owner; code and contracts in English.

| agent | owns | in -> out |
|---|---|---|
| `sourcePrepAgent/` | trim scanned sheets, levels/knockout, cut-outs (rembg, photocraft), original-preserving `derived.json` | raw project folder -> `images/ drawings/ diagrams/ sources/ derived.json` |
| `portfolioAgent/` | the book: host-LLM book plan -> grid/bleed/photo-set layout -> guardrails -> PDF/PPTX/PNG (local + DesignCraft backends) | `book-plan.json` + manifest -> `book.pdf`, `scenes/`, `qa.json`, `attempts/NN` |
| `reviewAgent/` | fresh-review gate, critic rubric, blind runs, benchmarks, human review protocol | PNG frames + hashes -> `review.json`, `benchmarks/reports/*.json` |
| (`../pascal-agents/DiagramAgent`) | diagrams: concept (diagram-design skill) + overlays on real drawings | `diagram-set/v1` |
| (`../pascal-agents/pptAgent`) | deck design system, palettes | `DESIGN.md`, `layout/v1` |

Shared code: `../../backend/common` (`portfolio_agent.core`: geometry, assets, guardrails; JSON schemas in `contracts/`). Plugin pieces at this folder's root: `.claude-plugin/`, `.codex-plugin/`, `skills/` (host-facing workflows; each skill names the agent that owns it), `scripts/portfolio.py` (single CLI entry).

## Run (from this folder)
```
python scripts/portfolio.py prepare|cutout <project> ...        # sourcePrepAgent
python scripts/portfolio.py compose <project> <book-plan.json> <out> --width-mm 297 --height-mm 210 --bleed-mm 3   # portfolioAgent
python scripts/portfolio.py review-context|record-review|finalize <out> ...      # reviewAgent
python -m pytest ../../backend/common/tests portfolioAgent/tests sourcePrepAgent/tests reviewAgent/tests -q
```
Import name stays `portfolio_agent` (PEP 420 namespace over the agents' `src/` roots; `backend/common/src/pascal_bootstrap.py` sets `sys.path`). Never add `__init__.py` to `portfolio_agent/` or `portfolio_agent/engine/`.
