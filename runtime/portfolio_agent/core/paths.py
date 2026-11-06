"""Plugin-root relative locations. The only place that knows where data lives."""
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
PATTERNS_FILE = PLUGIN_ROOT / "knowledge" / "patterns" / "layout-patterns.json"
SCENE_SCHEMA = PLUGIN_ROOT / "contracts" / "scene-document.schema.json"
BACKENDS_DIR = PLUGIN_ROOT / "backends"
CASES_APPROVED_DIR = PLUGIN_ROOT / "cases" / "approved"
