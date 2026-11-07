"""Import an edited native document as a separate, explicitly unverified attempt.

Ledger recovery: stop the API and all other writers first, back up ledger.jsonl,
then in the repository environment run Python and call:

    from pathlib import Path
    from pascal_api.books.native_import import recover_pending_ledger
    recover_pending_ledger(Path(r"<project directory>"), "02")

The function is idempotent for a complete identical existing entry. A truncated
or conflicting ledger is preserved and rejected; inspect the backup and repair
it explicitly before retrying. This is not safe with concurrent processes.
"""
import hashlib
import json
import math
import re
import shutil
import stat
import time
import zipfile
from pathlib import Path, PurePosixPath

import fitz

from ..gateways import agents

MAX_PAGE_PIXELS = 50_000_000
MAX_TOTAL_PIXELS = 100_000_000
MAX_PREVIEW_BYTES = 256 * 1024 * 1024
PREVIEW_DPI = 96


def _validate_page_size(width: float, height: float, index: int) -> int:
    if not math.isfinite(width) or not math.isfinite(height) or width <= 0 or height <= 0:
        raise ValueError(f"Edited PDF page {index} has invalid dimensions")
    # A rounding pixel on each edge safely bounds the renderer's integer device rectangle.
    pixels = (math.ceil(width * PREVIEW_DPI / 72) + 1) * (math.ceil(height * PREVIEW_DPI / 72) + 1)
    if pixels > MAX_PAGE_PIXELS:
        raise ValueError(f"Edited PDF page {index} exceeds the per-page pixel limit")
    return pixels


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_link_or_reparse(path: Path) -> bool:
    return path.is_symlink() or bool(getattr(path.lstat(), "st_file_attributes", 0) & 0x400)


def _append_ledger(attempts: Path, entry: dict) -> None:
    with (attempts / "ledger.jsonl").open("a", encoding="utf-8") as ledger:
        ledger.write(json.dumps(entry) + "\n")


def recover_pending_ledger(project: Path, attempt: str) -> str:
    """Reconcile one pending marker offline; preserve malformed/conflicting ledgers."""
    if not re.fullmatch(r"[0-9]{2}", attempt):
        raise ValueError("Attempt must be a two-digit identifier")
    attempts = Path(project) / "out" / "attempts"
    target = attempts / attempt
    if not attempts.is_dir() or _is_link_or_reparse(attempts) or not target.is_dir() or _is_link_or_reparse(target):
        raise ValueError("Attempt directory missing or linked")
    marker = target / "ledger-pending.json"
    ledger = attempts / "ledger.jsonl"
    if ledger.is_symlink() or (ledger.exists() and _is_link_or_reparse(ledger)):
        raise ValueError("Linked ledger refused")
    rows = []
    if ledger.exists():
        raw = ledger.read_text(encoding="utf-8")
        if raw and not raw.endswith("\n"):
            raise ValueError("Ledger has an incomplete final line; preserve and inspect it before recovery")
        try:
            rows = [json.loads(line) for line in raw.splitlines()]
        except (ValueError, TypeError) as exc:
            raise ValueError("Ledger contains invalid JSON; preserve and inspect it before recovery") from exc
        if any(not isinstance(row, dict) for row in rows):
            raise ValueError("Ledger contains a non-object record")
    matches = [row for row in rows if row.get("attempt") == attempt]
    if len(matches) > 1:
        raise ValueError("Ledger contains duplicate attempt records")
    if marker.is_symlink():
        raise ValueError("Linked pending marker refused")
    if not marker.exists():
        if len(matches) == 1:
            return "already_recorded"
        raise ValueError("No pending marker or recorded attempt")
    if _is_link_or_reparse(marker):
        raise ValueError("Linked pending marker refused")
    entry = json.loads(marker.read_text(encoding="utf-8"))
    if not isinstance(entry, dict) or entry.get("attempt") != attempt or entry.get("author") != "native_import":
        raise ValueError("Invalid pending ledger entry")
    if matches and matches[0] != entry:
        raise ValueError("Ledger already contains a conflicting attempt record")
    if not matches:
        _append_ledger(attempts, entry)
    marker.unlink()
    return "already_recorded" if matches else "appended"


def _validate_native_archive(path: Path) -> None:
    """Reject unsafe archive entries and bound decompression before invoking the CLI."""
    try:
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            if not entries or len(entries) > 10000:
                raise ValueError("Archive contains an invalid number of entries")
            names = set()
            total = 0
            for entry in entries:
                name = entry.filename
                parts = name.rstrip("/").split("/")
                if (not name or entry.orig_filename != name or "\\" in name or name.startswith("/") or any(p in ("", ".", "..") or ":" in p for p in parts)
                        or name.casefold() in names or stat.S_ISLNK(entry.external_attr >> 16) or entry.flag_bits & 1):
                    raise ValueError("Unsafe archive entry")
                names.add(name.casefold())
                total += entry.file_size
                if (entry.file_size > 128 * 1024 * 1024 or total > 256 * 1024 * 1024
                        or (entry.file_size > 1024 * 1024 and entry.file_size > max(entry.compress_size, 1) * 1000)):
                    raise ValueError("Archive exceeds decompression limits")
            if "document.json" not in archive.namelist() or archive.getinfo("document.json").is_dir():
                raise ValueError("Archive has no document.json")
            if archive.testzip() is not None:
                raise ValueError("Archive integrity check failed")
    except (zipfile.BadZipFile, NotImplementedError, RuntimeError) as exc:
        raise ValueError(f"Invalid DesignCraft archive: {exc}") from exc


def _source_evidence(project: Path, parent: str, staging: Path) -> dict:
    """Copy the parent's source manifest and check each original and derived asset."""
    parent_dir = project / "out" / "attempts" / parent
    manifest = parent_dir / "source-manifest.json"
    if not manifest.is_file():
        manifest = parent_dir / "manifest.json"
    evidence = {"manifest_sha256": None, "assets": [], "issues": [], "status": "unverified"}
    try:
        if not manifest.is_file() or _is_link_or_reparse(manifest):
            raise ValueError("Parent source manifest missing or symlinked")
        if manifest.stat().st_size > 10 * 1024 * 1024:
            raise ValueError("Parent source manifest exceeds size limit")
        raw = manifest.read_bytes()
        (staging / "source-manifest.json").write_bytes(raw)
        evidence["manifest_sha256"] = hashlib.sha256(raw).hexdigest()
        data = json.loads(raw)
        items = data.get("assets") if isinstance(data, dict) else None
        if not isinstance(items, list) or not items:
            raise ValueError("Parent source manifest has no assets")
        expected = {}
        for asset in items:
            if not isinstance(asset, dict):
                raise ValueError("Invalid asset record")
            records = [(asset.get("relative_path"), asset.get("sha256"))]
            if asset.get("source_transform") is not None:
                transform = asset["source_transform"]
                if not isinstance(transform, dict):
                    raise ValueError("Invalid source transform")
                records.append((transform.get("source"), transform.get("source_sha256")))
            for record_index, (name, digest) in enumerate(records):
                if not isinstance(name, str) or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                    raise ValueError("Missing or invalid source path/hash")
                parts = name.split("/")
                if ("\\" in name or any(part in ("", ".", "..") or ":" in part for part in parts)
                        or len(parts) < 2 or parts[0] not in (("images", "drawings", "diagrams") if record_index == 0 else ("sources",))
                        or PurePosixPath(name).is_absolute()):
                    raise ValueError(f"Unsafe source path: {name}")
                if name in expected and expected[name] != digest:
                    raise ValueError(f"Conflicting hashes for source: {name}")
                expected[name] = digest
        for name, digest in sorted(expected.items()):
            path = project.joinpath(*name.split("/"))
            current = project
            for part in name.split("/"):
                current = current / part
                if _is_link_or_reparse(current):
                    raise ValueError(f"Symlink in source path: {name}")
            if not path.is_file() or not path.resolve().is_relative_to(project.resolve()) or _sha(path) != digest:
                raise ValueError(f"Source missing or hash changed: {name}")
            evidence["assets"].append({"path": name, "sha256": digest})
        evidence["status"] = "verified"
    except (OSError, ValueError, TypeError, UnicodeDecodeError) as exc:
        evidence["issues"].append(str(exc))
    return evidence


def import_attempt(project: Path, parent: str, staging: Path, log) -> dict:
    """Work in the request's unique staging directory; publish only after a complete render."""
    native = staging / "book.designcraft"
    pdf = staging / "book.pdf"
    try:
        parent_native = project / "out" / "attempts" / parent / "book.designcraft"
        parent_hash = _sha(parent_native)
        source_evidence = _source_evidence(project, parent, staging)
        _validate_native_archive(native)
        log("Rendering the edited DesignCraft document to PDF")
        agents.render_designcraft_pdf(native, pdf)
        preview = staging / "preview"
        preview.mkdir()
        hashes = {}
        with fitz.open(pdf) as document:
            count = document.page_count
            if not 1 <= count <= 200:
                raise ValueError("Edited PDF must contain 1 to 200 pages")
            total_pixels = sum(_validate_page_size(page.rect.width, page.rect.height, index) for index, page in enumerate(document, 1))
            if total_pixels > MAX_TOTAL_PIXELS:
                raise ValueError("Edited PDF exceeds the total pixel budget for previews")
            preview_bytes = 0
            for index, page in enumerate(document, 1):
                path = preview / f"page-{index:02d}.png"
                page.get_pixmap(dpi=PREVIEW_DPI, colorspace=fitz.csRGB, alpha=False).save(path)
                preview_bytes += path.stat().st_size
                if preview_bytes > MAX_PREVIEW_BYTES:
                    raise ValueError("Edited PDF exceeds the total preview file size limit")
                hashes[path.name] = _sha(path)
        info = {"parent_attempt": parent, "parent_native_sha256": parent_hash, "parent_relation": "comparison_only", "derivation_verified": False,
                "source_evidence": source_evidence, "native_sha256": _sha(native), "pdf_sha256": _sha(pdf),
                "preview_source": "edited_pdf", "preview_dpi": PREVIEW_DPI, "preview_colorspace": "RGB", "preview_alpha": False,
                "structural_validation_passed": True, "structural_validation_scope": "PDF opened; bounded page count and dimensions; all pages rendered to PNG",
                "pages": count, "preview_sha256": hashes}
        (staging / "import.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
        issue = {"code": "NATIVE_EDIT_UNVERIFIED", "details": "Edited document content, sources and layout require independent human verification; scene-level QA was not run."}
        blocking = [issue]
        if source_evidence["status"] != "verified":
            blocking.append({"code": "SOURCE_PROVENANCE_UNVERIFIED", "details": "; ".join(source_evidence["issues"])})
        qa = {"gate_pass": False, "blocking_issues": blocking, "advisory_issues": [], "native_edit": info,
              "extra_exporters": {"designcraft": {"notes": [issue["details"]]}}}
        (staging / "qa.json").write_text(json.dumps(qa, indent=1), encoding="utf-8")
        attempts = project / "out" / "attempts"
        attempts.mkdir(parents=True, exist_ok=True)
        numbers = [int(p.name) for p in attempts.iterdir() if p.is_dir() and len(p.name) == 2 and p.name.isdigit()]
        number = max(numbers, default=0) + 1
        if number > 99:
            raise ValueError("Attempt limit reached (99)")
        target = attempts / f"{number:02d}"
        entry = {"attempt": target.name, "time": time.strftime("%Y-%m-%dT%H:%M:%S"), "author": "native_import", "condition": "edited_designcraft",
                 "gate_pass": False, "blocking": [i["code"] for i in blocking], "advisory": [], "plan_sha256": None, "pages": count}
        (staging / "ledger-pending.json").write_text(json.dumps(entry, indent=1), encoding="utf-8")
        staging.rename(target)
        try:
            _append_ledger(attempts, entry)
            (target / "ledger-pending.json").unlink()
        except OSError as exc:
            raise RuntimeError(f"Attempt {target.name} saved; ledger pending at {target / 'ledger-pending.json'}. Retry via POST /projects/{{id}}/attempts/{target.name}/recover-ledger: {exc}") from exc
        log(f"Created unverified attempt {target.name}")
        return {"attempt": target.name, "pages": count, "gate_pass": False, "blocking": blocking}
    finally:
        if staging.exists() and staging.resolve().parent == (project / "out" / ".native-imports").resolve():
            shutil.rmtree(staging)
