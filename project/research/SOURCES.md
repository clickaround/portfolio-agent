# SOURCES — 1차 출처와 증거 등급
Checked 2026-11-04 (UTC/KST); remote repositories and documentation change continuously. `repos.lock.json` captures a point-in-time GitHub commit, **not** a promise that its code works.

## Official engineering instructions
- OpenAI, [Iterating Development Workflows with Codex](https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex) — persistent `AGENTS.md`, `GOALS.md`, `PLANS.md`, bounded build files and evidence logs. `DOC_REPORTED`.
- OpenAI, [Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) — minimize bloated context/skills, keep focused triggers. `DOC_REPORTED`.
- OpenAI, [Plugin packaging](https://developers.openai.com/plugins/build/plugins) — root `plugin.json`, `skills/`, optional `mcp.json`; legacy `.codex-plugin` fallback. `DOC_REPORTED`.
- [Agent Plugins Specification 1.0.0](https://agent-plugins.org/specification) — portable plugin manifest and discovery. `DOC_REPORTED`.
- Anthropic, [CLAUDE.md guidance](https://support.claude.com/en/articles/14553240-give-claude-context-claude-md-and-better-prompts) — Claude project instructions. `DOC_REPORTED`.
- Anthropic, [Claude Code plugin example](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/example-plugin) — `.claude-plugin/plugin.json` and Skills. `CODE_INSPECTED` for example structure only.
- CMU SEI, [Attribute-Driven Design](https://www.sei.cmu.edu/library/attribute-driven-design-method-collection/) and [ATAM](https://www.sei.cmu.edu/library/architecture-tradeoff-analysis-method-collection/) — requirements-driven architecture and tradeoff review. `DOC_REPORTED`.
- [arc42](https://arc42.org/documentation/) and [C4](https://c4model.com/diagrams) — architecture communication, not performance proof.

## Repositories and evaluation
See `repos.lock.json` for exact commit SHAs. Key implementation entrypoints previously **read as source text**, but not run:
- AutoDesign: `agent_skills/autodesign-poster/SKILL.md`, `eval/README.md`, `autodesign/evaluator/`.
- DeepSlides: `src/open_deep_research/graph.py` (LangGraph, ablation switches).
- GDB: `src/gdb/tasks/layout.py`, `src/gdb/metrics/core.py` (evaluation tasks, geometry/IoU etc.).
- SlidesGen-Bench: `eval/aesthetics_metrics.py`, `eval/calculate_quiz_accuracy.py` (aesthetic and quiz metrics).
- Paper2Poster: `Paper2Poster-eval/eval_poster_pipeline.py` (question-answer evaluation).
- DeckBench: `metrics/deck_metrics.py` (deck similarity, order, assignment).
- Editable-Design: `skills/editable-design/SKILL.md` (**fixed canvas poster**, explicitly not slide decks).
- Diagram Design: `skills/diagram-design/SKILL.md`, `scripts/self_check.py`, `type-axonometric-plan.md` (editorial diagram grammar; not a CAD import engine).
- HarnessRouter: `README.md`, `protocol/README.md`, `protocol/conformance/README.md` (UHP API/conformance, not portfolio aesthetics).
- HarnessRouter Slides Kit: `https://github.com/HarnessRouter/starter-kit/tree/main/kits/slides` (**special commercial license**).
- OpenPencil: `https://github.com/open-pencil/open-pencil` and CLI/MCP/SDK README claims. **Drawing fidelity unverified.**
- GenOffice: `https://github.com/genspark-ai/genoffice` and CLI/MCP/Slides README claims. **Drawing fidelity unverified.**

## Academic papers and benchmarks (detailed reading scheduled P02/P03)
- GDB / GraphicDesignBench: https://arxiv.org/abs/2604.04192 ; https://github.com/lica-world/GDB
- DeepSlides: https://github.com/sxswz213/DeepSlides
- SlidesGen-Bench: https://github.com/YunqiaoYang/SlidesGen-Bench
- AutoDesign / PosterBench: https://github.com/Yaxin9Luo/AutoDesign
- Paper2Poster: https://github.com/Paper2Poster/Paper2Poster
- DECKBench: https://github.com/morgan-heisler/DeckBench
- Editable-Design: https://github.com/yejy53/Editable-Design
- LayoutPrompter: https://github.com/tanshinjie/layout-prompter

**Evidence gap:** all paper appendices, full benchmarks, independent model runs, local installed versions, professional architecture portfolio quality studies remain NOT_REPRODUCED. Recording an author score is not reproducing it.
