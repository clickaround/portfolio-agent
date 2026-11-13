# reviewAgent — independent review

Guide for people and coding agents working in this folder. Identity: `SOUL.md` (C1). Guardrails: `guardrails/GUARDRAILS.md` (C2). Harness² manifest: `harness.yaml`. `RULES.md` is generated from the guardrails and the tool guidance; never edit it. Layout follows `../baseAgent/MODULE.md` (gitagent + Harness²).

- Code: `src/portfolio_agent/engine/review.py` (`review-context`, `record-review`, `finalize`; declared in `tools/`). Rubric: `knowledge/critic-rubric.md` (8 dimensions).
- Blind protocol: randomised X/Y/Z labels, key in `.cache/_unblind_key*.json`, critic = fresh `claude -p` with Read only; one LLM critic is noise +-0.07 (never claim quality from it). Human blind pairwise review is the real evidence (`benchmarks/HUMAN_REVIEW.md`).
- Benchmarks: `benchmarks/` (SPEC, protocol, runners; `reports/<run>.json` = blind runs incl. predictions checked, AHE-style).
- Depends on `backend/packages/portfolio-core` (core) only.
