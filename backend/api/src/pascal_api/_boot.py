"""Puts backend/common/src on sys.path and every portfolio_agent source root after it. Import this before any portfolio_agent import."""
import sys
from pathlib import Path

_COMMON_SRC = Path(__file__).resolve().parents[3] / "common" / "src"      # backend/api/src/pascal_api -> backend/common/src
if str(_COMMON_SRC) not in sys.path:
    sys.path.insert(0, str(_COMMON_SRC))
import pascal_bootstrap  # noqa: E402

WORKSPACE = pascal_bootstrap.setup()
