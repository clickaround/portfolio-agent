"""Project storage on disk. One folder per project, same shape the agents read:

    <data_dir>/projects/<id>/{images,drawings,diagrams}/  sources/  project.md  derived.json  book-plan.json  plans/  out/attempts/NN
"""
import json
import re
import shutil
import time
from pathlib import Path

from ..exceptions import ApiError, bad_request, not_found

ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
ASSET_KINDS = ("images", "drawings", "diagrams")
FILE_KINDS = ASSET_KINDS + ("sources",)
EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp", ".svg", ".pdf"}
NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def safe_filename(name: str) -> str:
    base = Path(name.replace("\\", "/")).name
    base = NAME_RE.sub("_", base).lstrip(".")
    if not base or Path(base).suffix.lower() not in EXTS:
        raise bad_request("bad_filename", f"file name {name!r}: allowed extensions {sorted(EXTS)}")
    return base


class ProjectStore:
    def __init__(self, data_dir: Path):
        self.root = Path(data_dir) / "projects"
        self.root.mkdir(parents=True, exist_ok=True)

    def dir(self, pid: str) -> Path:
        if not ID_RE.match(pid or ""):
            raise bad_request("bad_project_id", "project id: lowercase letters, digits, - and _ (max 64)")
        d = self.root / pid
        if not d.is_dir():
            raise not_found(f"project {pid!r}")
        return d

    def create(self, pid: str, title: str = "", brief: str = "") -> Path:
        if not ID_RE.match(pid or ""):
            raise bad_request("bad_project_id", "project id: lowercase letters, digits, - and _ (max 64)")
        d = self.root / pid
        if d.exists():
            raise ApiError(409, "exists", f"project {pid!r} already exists")
        for k in ASSET_KINDS + ("sources",):
            (d / k).mkdir(parents=True)
        (d / "project.md").write_text(brief or f"# {title or pid}\ndomain: architecture\nkeywords: \n", encoding="utf-8")
        (d / "meta.json").write_text(json.dumps({"id": pid, "title": title or pid, "created": time.strftime("%Y-%m-%dT%H:%M:%S")}, indent=1), encoding="utf-8")
        return d

    def meta(self, pid: str) -> dict:
        d = self.dir(pid)
        m = json.loads((d / "meta.json").read_text(encoding="utf-8")) if (d / "meta.json").is_file() else {"id": pid, "title": pid}
        m["assets"] = {k: len([p for p in (d / k).iterdir() if p.is_file()]) for k in ASSET_KINDS}
        m["has_plan"] = (d / "book-plan.json").is_file()
        m["attempts"] = len(list((d / "out" / "attempts").glob("[0-9][0-9]"))) if (d / "out" / "attempts").is_dir() else 0
        return m

    def list(self) -> list:
        return [self.meta(p.name) for p in sorted(self.root.iterdir()) if p.is_dir() and ID_RE.match(p.name)]

    def delete(self, pid: str):
        shutil.rmtree(self.dir(pid))

    def add_asset(self, pid: str, kind: str, filename: str, stream, max_bytes: int) -> Path:
        if kind not in ASSET_KINDS:
            raise bad_request("bad_kind", f"kind must be one of {ASSET_KINDS}")
        d = self.dir(pid) / kind
        target = d / safe_filename(filename)
        written = 0
        with target.open("wb") as f:
            while chunk := stream.read(1 << 20):
                written += len(chunk)
                if written > max_bytes:
                    f.close()
                    target.unlink(missing_ok=True)
                    raise ApiError(413, "too_large", f"upload exceeds {max_bytes // (1 << 20)} MB")
                f.write(chunk)
        return target

    def asset_path(self, pid: str, kind: str, name: str) -> Path:
        if kind not in FILE_KINDS:
            raise bad_request("bad_kind", f"kind must be one of {FILE_KINDS}")
        base = self.dir(pid).resolve()
        p = (base / kind / safe_filename(name)).resolve()
        if base not in p.parents or not p.is_file():
            raise not_found(f"{kind}/{name}")
        return p

    def attempts_dir(self, pid: str) -> Path:
        return self.dir(pid) / "out" / "attempts"

    def attempt_dir(self, pid: str, nn: str) -> Path:
        if not re.fullmatch(r"\d\d", nn or ""):
            raise bad_request("bad_attempt", "attempt is a two-digit number, e.g. 03")
        d = self.attempts_dir(pid) / nn
        if not d.is_dir():
            raise not_found(f"attempt {nn}")
        return d
