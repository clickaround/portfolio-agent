#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONDONTWRITEBYTECODE=1
python scripts/validate_package.py
python -m unittest discover -s tests -v
python scripts/task_status.py --ready
python scripts/clone_repos.py --id designcraft
printf '
Paste prompts/START_HERE_KO.md into Codex or Claude Code.
'
