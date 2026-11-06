#!/usr/bin/env python3
"""Single entry point for Claude Code and Codex: `python scripts/portfolio.py run|compose|prepare|cutout|... ` (UTF-8 safe, no install needed).
Run from the plugin root (agents/portfolio-agents). Puts every portfolio_agent source root on sys.path (backend/common/src/pascal_bootstrap.py)."""
import os, sys
from pathlib import Path
os.environ.setdefault("PYTHONUTF8", "1"); os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1"); sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "backend" / "common" / "src"))
import pascal_bootstrap; pascal_bootstrap.setup()
from portfolio_agent.cli import main
sys.exit(main())
