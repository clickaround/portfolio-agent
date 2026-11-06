"""Runtime settings, read from the environment on every call (tests override them)."""
import os
from dataclasses import dataclass
from pathlib import Path

from ._boot import WORKSPACE


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    claude_bin: str
    max_upload_mb: int
    llm_timeout_s: int
    workers: int
    cors_origins: tuple


def get_settings() -> Settings:
    return Settings(
        data_dir=Path(os.environ.get("PASCAL_DATA_DIR") or WORKSPACE / ".cache" / "pascal-data"),
        claude_bin=os.environ.get("PASCAL_CLAUDE_BIN", "claude"),
        max_upload_mb=int(os.environ.get("PASCAL_MAX_UPLOAD_MB", "100")),
        llm_timeout_s=int(os.environ.get("PASCAL_LLM_TIMEOUT_S", "900")),
        workers=int(os.environ.get("PASCAL_WORKERS", "2")),
        cors_origins=tuple(x for x in os.environ.get("PASCAL_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if x),
    )
