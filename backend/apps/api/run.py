#!/usr/bin/env python3
"""Start the API: `python backend/api/run.py [--host 127.0.0.1] [--port 8000]`. Data under PASCAL_DATA_DIR (default <workspace>/.cache/pascal-data)."""
import argparse
import os
import sys
from pathlib import Path

os.environ.setdefault("PYTHONUTF8", "1")
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import uvicorn  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    a = ap.parse_args()
    uvicorn.run("pascal_api.main:create_app", factory=True, host=a.host, port=a.port, reload=False)
