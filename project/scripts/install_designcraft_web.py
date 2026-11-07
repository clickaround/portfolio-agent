#!/usr/bin/env python3
"""Install the pinned official DesignCraft web bundle into the workspace cache."""
from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

URL = "https://github.com/storytold/designcraft/releases/download/v0.17.0/designcraft-web-0.17.0.zip"
SHA256 = "b8d81cccf9778c4fff22111bce915b33c3ff6dc7de40a51e4cba7f4b62a0875f"
ARCHIVE = "designcraft-web-0.17.0.zip"
DIRECTORY = "designcraft-web-0.17.0"
ROOT = Path(__file__).resolve().parents[2] / ".cache" / "bin" / "designcraft" / "web"
PUBLIC = Path(__file__).resolve().parents[2] / "frontend" / "public" / "designcraft-editor"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_checked(archive: Path, target: Path) -> None:
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            name = item.filename
            path = PurePosixPath(name)
            if ("\\" in name or ":" in name or path.is_absolute() or ".." in path.parts
                    or not path.parts or path.parts[0] != DIRECTORY
                    or (item.external_attr >> 16) & 0o170000 == 0o120000):
                raise ValueError(f"Unsafe ZIP member: {name}")
        if sum(item.file_size for item in z.infolist()) > 1024 * 1024 * 1024:
            raise ValueError("ZIP exceeds extraction size limit")
        z.extractall(target)


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    archive = ROOT / ARCHIVE
    installed = ROOT / "dist" / DIRECTORY
    if archive.exists() and digest(archive) != SHA256:
        raise RuntimeError(f"Existing archive hash mismatch; preserved: {archive}")
    for destination in (installed, PUBLIC):
        if destination.exists() and not (destination / "index.html").is_file():
            raise RuntimeError(f"Existing destination incomplete; preserved: {destination}")
    with tempfile.TemporaryDirectory(prefix="install-", dir=ROOT) as tmp:
        staging = Path(tmp)
        if not archive.exists():
            download = staging / ARCHIVE
            with urllib.request.urlopen(URL, timeout=120) as response, download.open("wb") as f:
                shutil.copyfileobj(response, f)
            if digest(download) != SHA256:
                raise RuntimeError("Downloaded archive hash mismatch")
            # Do not replace a file another installer created while downloading.
            try:
                with archive.open("xb") as f, download.open("rb") as src:
                    shutil.copyfileobj(src, f)
            except FileExistsError:
                if digest(archive) != SHA256:
                    raise RuntimeError(f"Concurrent archive hash mismatch; preserved: {archive}")
        extract_checked(archive, staging)
        if not (staging / DIRECTORY / "index.html").is_file():
            raise RuntimeError("Archive does not contain expected index.html")
        source = staging / DIRECTORY
        if not installed.exists():
            installed.parent.mkdir(exist_ok=True)
            shutil.copytree(source, staging / "cache-copy")
            os.rename(staging / "cache-copy", installed)
            print(f"Installed cache: {installed}")
        else:
            print(f"Existing cache preserved: {installed}")
        if not PUBLIC.exists():
            PUBLIC.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix="designcraft-stage-", dir=PUBLIC.parent) as public_tmp:
                copy = Path(public_tmp) / "bundle"
                shutil.copytree(source, copy)
                os.rename(copy, PUBLIC)
            print(f"Installed public editor: {PUBLIC}")
        else:
            print(f"Existing public editor preserved: {PUBLIC}")


if __name__ == "__main__":
    main()
