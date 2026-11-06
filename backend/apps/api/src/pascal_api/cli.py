"""Console entry: `uv run pascal-api --port 8000` (same as backend/apps/api/run.py)."""
import argparse
import os


def serve() -> None:
    import uvicorn

    os.environ.setdefault("PYTHONUTF8", "1")
    ap = argparse.ArgumentParser(prog="pascal-api")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    a = ap.parse_args()
    uvicorn.run("pascal_api.main:create_app", factory=True, host=a.host, port=a.port)
