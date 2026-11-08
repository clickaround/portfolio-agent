#!/usr/bin/env python3
"""Publish the locally built Pascal editor without replacing unmanaged files."""
from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "editor" / "designcraft" / "dist" / "web"
SOURCE_ROOT = ROOT / "editor" / "designcraft"
TARGET = ROOT / "frontend" / "public" / "pascal-editor"
MARKER = ".pascal-editor-build"


def main() -> None:
    if not (SOURCE / "index.html").is_file() or not list(SOURCE.glob("*.wasm")):
        raise RuntimeError(f"Build the Rust web editor first: {SOURCE}")
    if TARGET.exists() and (TARGET.is_symlink() or not (TARGET / MARKER).is_file()):
        raise RuntimeError(f"Existing unmanaged editor directory preserved: {TARGET}")
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="pascal-editor-", dir=TARGET.parent) as tmp:
        staging = Path(tmp) / "new"
        shutil.copytree(SOURCE, staging)
        for name in ("LICENSE-MIT", "LICENSE-APACHE", "NOTICE", "ASSETS.md"):
            shutil.copy2(SOURCE_ROOT / name, staging / name)
        shutil.copytree(SOURCE_ROOT / "licenses", staging / "licenses")
        fonts = staging / "assets" / "fonts"
        fonts.mkdir(parents=True, exist_ok=True)
        for notice in (SOURCE_ROOT / "assets" / "fonts").glob("OFL-*.txt"):
            shutil.copy2(notice, fonts / notice.name)
        (staging / MARKER).write_text("Built from editor/designcraft\n", encoding="utf-8")
        backup = Path(tmp) / "previous"
        if TARGET.exists():
            TARGET.rename(backup)
        try:
            staging.rename(TARGET)
        except OSError:
            if backup.exists():
                backup.rename(TARGET)
            raise
    print(f"Installed Pascal editor: {TARGET}")


if __name__ == "__main__":
    main()
