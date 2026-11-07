"""Where things live. The only module that knows the workspace layout (so no other module counts `parents[n]`).

The workspace root is found by walking up from this file to the directory whose pyproject.toml declares `[tool.uv.workspace]`
(or from `PASCAL_WORKSPACE`). Agents are installed editable from the repository, so these paths are real folders.
"""
import os
import importlib.util
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def find_workspace() -> Path:
    env = os.environ.get("PASCAL_WORKSPACE")
    if env:
        return Path(env).resolve()
    for p in Path(__file__).resolve().parents:
        f = p / "pyproject.toml"
        if f.is_file() and "[tool.uv.workspace]" in f.read_text(encoding="utf-8", errors="ignore"):
            return p
    spec = importlib.util.find_spec("portfolio_runtime_data")
    if spec and spec.origin:
        return Path(spec.origin).resolve().parent
    raise RuntimeError("workspace root not found: set PASCAL_WORKSPACE or run from the repository checkout")


WORKSPACE = find_workspace()
AGENTS_DIR = WORKSPACE / "agents"
PLUGIN = AGENTS_DIR / "portfolio-plugin"              # plugin root: .claude-plugin, skills/, scripts/portfolio.py
PORTFOLIO_AGENT = AGENTS_DIR / "portfolioAgent"
SOURCEPREP_AGENT = AGENTS_DIR / "sourcePrepAgent"
REVIEW_AGENT = AGENTS_DIR / "reviewAgent"
PROJECT = WORKSPACE / "project"                       # governance docs, tasks, research, evidence (not code)
_installed = (WORKSPACE / "__init__.py").is_file() and WORKSPACE.name == "portfolio_runtime_data"
_user_data = Path(os.environ.get("PASCAL_DATA_DIR", Path.home() / ".portfolio-agent")).expanduser().resolve()
CACHE_DIR = _user_data / "cache" if _installed else WORKSPACE / ".cache"

SCHEMAS_DIR = Path(__file__).resolve().parent / "schemas"   # JSON schemas ship with the code that validates them
KNOWLEDGE_DIR = PORTFOLIO_AGENT / "knowledge"
PATTERNS_DIR = KNOWLEDGE_DIR / "patterns"
PATTERNS_FILE = PATTERNS_DIR / "layout-patterns.json"
SCENE_SCHEMA = SCHEMAS_DIR / "scene-document.schema.json"
BOOK_PLAN_SCHEMA = SCHEMAS_DIR / "book-plan.schema.json"
BACKENDS_DIR = PORTFOLIO_AGENT / "backends"
CASES_APPROVED_DIR = _user_data / "cases" / "approved" if _installed else PROJECT / "cases" / "approved"
CRITIC_RUBRIC = REVIEW_AGENT / "knowledge" / "critic-rubric.md"
EXAMPLES_DIR = PORTFOLIO_AGENT / "examples"
