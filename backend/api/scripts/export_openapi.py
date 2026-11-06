#!/usr/bin/env python3
"""Write the OpenAPI contract the frontend codes against: backend/api/openapi.json. `--check` fails when the file is stale (CI / tests)."""
import json
import sys
import tempfile
from pathlib import Path

API = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(API / "src"))

from pascal_api.config import Settings  # noqa: E402
from pascal_api.main import create_app  # noqa: E402


def spec() -> dict:
    with tempfile.TemporaryDirectory() as td:
        s = Settings(data_dir=Path(td), claude_bin="claude", max_upload_mb=100, llm_timeout_s=900, workers=1, cors_origins=())
        return create_app(s).openapi()


if __name__ == "__main__":
    text = json.dumps(spec(), indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    target = API / "openapi.json"
    if "--check" in sys.argv:
        sys.exit(0 if target.is_file() and target.read_text(encoding="utf-8") == text else "openapi.json is stale: run backend/api/scripts/export_openapi.py")
    target.write_text(text, encoding="utf-8")
    print("wrote", target)
