> **ARCHIVED V2; historical validation only.** Current v3 authoritative docs: GOALS.md, PLANS.md, architecture/ARCHITECTURE_MAP.md, formats/, research/repos.lock.json.

# Training decision tree (defer until P08)

Observed failure → preferred first remedy:
- Invalid asset labels / missing context → better asset manifest, domain examples, human unknown flags.
- Geometric errors → deterministic layout constraints / clipping test.
- Same-looking pages → editorial grammar and diverse candidate generation.
- Good candidates but wrong winner → human pairwise labels → small ranker or preference predictor.
- All candidates bad → generation approach and qualified sample dataset, only later consider LoRA/SFT.
- PDF/vector loss → renderer/export engineering, not LLM training.
- Factual misstatements → source-grounding and verification, not aesthetic reward.

No training plan without (1) repeated measured error type; (2) consented sufficient dataset with disjoint heldout; (3) stable evaluation; (4) cost/quality ROI; (5) data privacy + deletion workflow. RTX 4090 availability does not justify starting training.
