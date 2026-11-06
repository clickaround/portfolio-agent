"""core.guardrails: everything that can refuse, flag or bound a portfolio - never anything that designs one.

policy      which issue codes BLOCK export and which only ADVISE; type-size floors (ADR-0009)
gates       deterministic checks on scenes, books and PDFs (G1-G3, G5 proxies)
grounding   advisory lexical check that page text comes from project.md (G4 proxy)
repair      bounded, logged auto-repair (font floor, margin nudge) - the one documented exception to "scripts never edit the artifact"
references  rights gate for reference cases (cases/RIGHTS_PROTOCOL.md)
The fresh-review binding lives in engine/review.py because it orchestrates files and reviewers, not rules."""
from . import gates, grounding, policy, references, repair  # noqa: F401
