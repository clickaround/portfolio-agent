#!/usr/bin/env python3
"""Single entry point for Claude Code and Codex: `python scripts/portfolio.py run|compose|prepare|cutout|... ` (UTF-8 safe).
Needs the workspace installed once: `uv sync` at the repository root (editable installs of the core + the three agents), then `uv run python scripts/portfolio.py ...`
(or `portfolio ...`, the console script of the same name)."""
import os
import sys

os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
sys.dont_write_bytecode = True

from portfolio_agent.cli import main  # noqa: E402

sys.exit(main())
