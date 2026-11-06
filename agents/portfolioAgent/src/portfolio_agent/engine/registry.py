"""Discovery of authors and backends. The ONLY place that knows concrete implementations.

Authors are importable packages under `portfolio_agent.authors.<name>` exposing `AUTHOR`.
Backends are loaded BY PATH from `<plugin>/backends/<name>/adapter.py` exposing `BACKEND`, so adding a backend never touches package code
and a broken backend cannot break the others.
"""
import importlib
import importlib.util
import sys
from portfolio_agent.core.paths import BACKENDS_DIR

_cache = {}


def list_backends():
    return sorted(p.parent.name for p in BACKENDS_DIR.glob("*/adapter.py"))


def get_backend(name):
    if name in _cache:
        return _cache[name]
    path = BACKENDS_DIR / name / "adapter.py"
    if not path.is_file():
        raise LookupError(f"backend {name!r} not found; available: {list_backends()}")
    spec = importlib.util.spec_from_file_location(f"pa_backend_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    _cache[name] = mod.BACKEND
    return mod.BACKEND


def get_author(name):
    try:
        return importlib.import_module(f"portfolio_agent.authors.{name}").AUTHOR
    except ModuleNotFoundError as e:
        raise LookupError(f"author {name!r} not found") from e
