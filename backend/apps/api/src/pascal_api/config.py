"""Runtime settings, read from the environment on every call (tests override them)."""
import os
from dataclasses import dataclass
from pathlib import Path

from .gateways.agents import workspace_root


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    claude_bin: str
    max_upload_mb: int
    llm_timeout_s: int
    workers: int
    cors_origins: tuple
    auth_url: str = ""
    auth_key: str = ""


def get_settings() -> Settings:
    local_auth = {}
    local_file = Path(__file__).resolve().parents[2] / ".env.local"
    if local_file.is_file():
        for line in local_file.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition("=")
            if separator and key in {"PASCAL_SUPABASE_URL", "PASCAL_SUPABASE_PUBLISHABLE_KEY"}:
                local_auth[key] = value.strip()
    return Settings(
        data_dir=Path(os.environ.get("PASCAL_DATA_DIR") or workspace_root() / ".cache" / "pascal-data"),
        claude_bin=os.environ.get("PASCAL_CLAUDE_BIN", "claude"),
        max_upload_mb=int(os.environ.get("PASCAL_MAX_UPLOAD_MB", "100")),
        llm_timeout_s=int(os.environ.get("PASCAL_LLM_TIMEOUT_S", "900")),
        workers=int(os.environ.get("PASCAL_WORKERS", "2")),
        cors_origins=tuple(x for x in os.environ.get("PASCAL_CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if x),
        auth_url=os.environ.get("PASCAL_SUPABASE_URL", local_auth.get("PASCAL_SUPABASE_URL", "")),
        auth_key=os.environ.get("PASCAL_SUPABASE_PUBLISHABLE_KEY", local_auth.get("PASCAL_SUPABASE_PUBLISHABLE_KEY", "")),
    )
