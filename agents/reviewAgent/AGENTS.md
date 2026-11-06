# reviewAgent — independent review

The engine never judges taste. This agent binds what must be reviewed (frames, scene hashes, rubric) into `review-context.json`, accepts a review only from a FRESH reviewer that copies the hashes, and promotes an attempt to `final/` only when blocking gates AND a fresh review passed.

- Code: `src/portfolio_agent/engine/review.py` (`review-context`, `record-review`, `finalize`). Rubric: `knowledge/critic-rubric.md` (8 dimensions).
- Blind protocol: randomised X/Y/Z labels, key in `.cache/_unblind_key*.json`, critic = fresh `claude -p` with Read only; one LLM critic is noise +-0.07 (never claim quality from it). Human blind pairwise review is the real evidence (`benchmarks/HUMAN_REVIEW.md`).
- Benchmarks: `benchmarks/` (SPEC, protocol, runners; `reports/<run>.json` = blind runs incl. predictions checked, AHE-style).
- Depends on `backend/packages/portfolio-core` (core) only.
