"""Loads the two stdlib check scripts shipped with the design package (scripts/check_layout.py, scripts/check_edit_diff.py) by path,
so there is ONE implementation of geometry/overlap and scene-diff rules for the CLI scripts and the engine."""
import importlib.util
from .paths import PLUGIN_ROOT


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, PLUGIN_ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CL = _load("check_layout", "scripts/check_layout.py")
CED = _load("check_edit_diff", "scripts/check_edit_diff.py")
