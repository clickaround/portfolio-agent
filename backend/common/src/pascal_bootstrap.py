"""One call puts every source root of the portfolio_agent namespace package on sys.path.

Entry scripts and conftest.py files do `import pascal_bootstrap` after adding THIS directory (the only path they must know:
backend/common/src) to sys.path - see agents/portfolio-agents/scripts/portfolio.py.
"""
import sys
from pathlib import Path

_COMMON = Path(__file__).resolve().parents[1]
_WORKSPACE = _COMMON.parents[1]
_HUB = _WORKSPACE / "agents" / "portfolio-agents"
SOURCE_ROOTS = [_COMMON / "src", _HUB / "portfolioAgent" / "src", _HUB / "sourcePrepAgent" / "src", _HUB / "reviewAgent" / "src"]


def setup():
    for p in reversed(SOURCE_ROOTS):
        s = str(p)
        if s not in sys.path:
            sys.path.insert(0, s)
    return _WORKSPACE
