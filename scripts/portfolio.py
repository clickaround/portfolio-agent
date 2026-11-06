#!/usr/bin/env python3
"""Single entry point for Claude Code and Codex: `python scripts/portfolio.py run|edit ...` (UTF-8 safe, no install needed)."""
import os, sys
from pathlib import Path
os.environ.setdefault("PYTHONUTF8", "1"); os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1"); sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "runtime"))
from portfolio_agent.cli import main
sys.exit(main())
