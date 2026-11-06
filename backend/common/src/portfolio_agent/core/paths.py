"""Workspace locations. The only place that knows where things live (agents/backend split, 2026-11-06).

portfolio_agent is a PEP 420 namespace package spread over source roots (see pascal_bootstrap.py):
  backend/common/src                           core (+ guardrails)                     <- shared by every agent
  agents/portfolio-agents/portfolioAgent/src   layout, authors, engine (pipeline ...), cli
  agents/portfolio-agents/sourcePrepAgent/src  engine.prepare / levels / cutout
  agents/portfolio-agents/reviewAgent/src      engine.review
"""
from pathlib import Path

COMMON = Path(__file__).resolve().parents[3]          # backend/common
WORKSPACE = COMMON.parents[1]
HUB = WORKSPACE / "agents" / "portfolio-agents"       # the plugin root
PORTFOLIO_AGENT = HUB / "portfolioAgent"
SOURCEPREP_AGENT = HUB / "sourcePrepAgent"
REVIEW_AGENT = HUB / "reviewAgent"
PROJECT = WORKSPACE / "project"                       # governance docs, tasks, research, evidence (not code)
CACHE_DIR = WORKSPACE / ".cache"                      # ignored: vendor clones, signed binaries, blind keys

CONTRACTS_DIR = COMMON / "contracts"
CHECKS_DIR = COMMON / "checks"
KNOWLEDGE_DIR = PORTFOLIO_AGENT / "knowledge"
PATTERNS_DIR = KNOWLEDGE_DIR / "patterns"
PATTERNS_FILE = PATTERNS_DIR / "layout-patterns.json"
SCENE_SCHEMA = CONTRACTS_DIR / "scene-document.schema.json"
BOOK_PLAN_SCHEMA = CONTRACTS_DIR / "book-plan.schema.json"
BACKENDS_DIR = PORTFOLIO_AGENT / "backends"
CASES_APPROVED_DIR = PROJECT / "cases" / "approved"
CRITIC_RUBRIC = REVIEW_AGENT / "knowledge" / "critic-rubric.md"
EXAMPLES_DIR = PORTFOLIO_AGENT / "examples"

SOURCE_ROOTS = [COMMON / "src", PORTFOLIO_AGENT / "src", SOURCEPREP_AGENT / "src", REVIEW_AGENT / "src"]
