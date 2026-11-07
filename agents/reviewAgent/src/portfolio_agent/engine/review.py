"""Fresh-review gate (AutoDesign-style, research/PAPER_NOTES_AUTODESIGN_HARNESS.md guardrail 3).

The engine never judges taste itself. It (1) binds what must be reviewed - preview frames, scene hashes, rubric - into
`review-context.json`; (2) accepts a review JSON only if it copies those bindings exactly, was produced by a *fresh* reviewer,
covers every frame, and has zero blockers with a mean >= PASS_MEAN; (3) `finalize` promotes the attempt only when the latest
attempt passed the blocking gates AND carries a passing fresh review.

Review JSON (written by the fresh reviewer, see knowledge/editorial/critic-rubric.md for the 8 dimensions, scores 0-1):
{"review_context_sha256": "...", "frame_hashes": {"page-01.png": "..."}, "reviewer_mode": "fresh_subagent"|"fresh_session"|"human",
 "reviewed_frames": [...], "dimension_scores": {"hierarchy": 0.7, ...}, "blockers": [], "issues": [...], "verdict": "pass"|"revise"|"fail"}
"""
import json
import time
from pathlib import Path, PurePosixPath

from portfolio_agent.core.sources.assets import sha256
from portfolio_agent.core.workspace import CRITIC_RUBRIC

RUBRIC = CRITIC_RUBRIC
DIMENSIONS = ("hierarchy", "composition_balance", "whitespace_intent", "typography", "sequence_narrative", "asset_fidelity", "domain_fit", "anti_template")
PASS_MEAN = 0.75
FRESH_MODES = {"fresh_subagent", "fresh_session", "human"}
NATIVE_CONFIRMATIONS = ("reviewed_exported_pages", "content_and_source_fidelity_confirmed", "page_geometry_and_clipping_confirmed")


class ReviewError(ValueError):
    pass


def _attempt_dir(out):
    att = sorted((Path(out) / "attempts").glob("[0-9][0-9]"))
    if not att:
        raise ReviewError("no attempts yet: run `compose`/`run` first")
    latest = att[-1]
    pending = latest / "ledger-pending.json"
    if pending.exists() or pending.is_symlink():
        raise ReviewError(f"attempt {latest.name} ledger is pending: reconcile {pending} before review")
    return latest


def _bound_files(att):
    return {name: sha256(att / name) for name in ("book.pdf", "book.pptx", "book.designcraft", "qa.json", "import.json", "source-manifest.json") if (att / name).is_file()}


def _source_evidence(att, meta):
    evidence = meta.get("source_evidence")
    if not isinstance(evidence, dict) or evidence.get("status") != "verified" or evidence.get("issues") != []:
        raise ValueError("source provenance is not verified")
    manifest_path = att / "source-manifest.json"
    parent = att.parent / meta["parent_attempt"]
    parent_manifest = parent / "source-manifest.json" if (parent / "source-manifest.json").is_file() else parent / "manifest.json"
    manifest_hash = evidence.get("manifest_sha256")
    for file in (manifest_path, parent_manifest):
        st = file.lstat()
        if file.is_symlink() or getattr(st, "st_file_attributes", 0) & 0x400 or not file.is_file():
            raise ValueError("source manifest symlink or reparse point refused")
    if not isinstance(manifest_hash, str) or sha256(manifest_path) != manifest_hash or sha256(parent_manifest) != manifest_hash:
        raise ValueError("source manifest missing or changed")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assets = manifest.get("assets")
    if not isinstance(assets, list) or not assets:
        raise ValueError("source manifest has no assets")
    expected = {}

    def add(path, digest, allowed):
        if not isinstance(path, str) or not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("invalid source path or SHA256")
        parts = PurePosixPath(path).parts
        if ("\\" in path or ":" in path or PurePosixPath(path).is_absolute() or len(parts) < 2
                or parts[0] not in allowed or any(p in (".", "..") for p in parts)):
            raise ValueError("source path escapes allowed directories")
        if path in expected and expected[path] != digest:
            raise ValueError("conflicting source hashes")
        expected[path] = digest

    for asset in assets:
        if not isinstance(asset, dict):
            raise ValueError("invalid manifest asset")
        add(asset.get("relative_path"), asset.get("sha256"), {"images", "drawings", "diagrams"})
        if asset.get("source_transform") is not None:
            transform = asset["source_transform"]
            if not isinstance(transform, dict):
                raise ValueError("invalid source transform")
            add(transform.get("source"), transform.get("source_sha256"), {"sources"})
    listed = evidence.get("assets")
    if not isinstance(listed, list) or any(not isinstance(x, dict) or set(x) != {"path", "sha256"} for x in listed):
        raise ValueError("invalid source evidence list")
    actual = {item["path"]: item["sha256"] for item in listed}
    if len(actual) != len(listed) or actual != expected:
        raise ValueError("source evidence does not match manifest")
    root = att.parents[2]
    for path, digest in expected.items():
        current = root
        for part in PurePosixPath(path).parts:
            current = current / part
            stat = current.lstat()
            if current.is_symlink() or getattr(stat, "st_file_attributes", 0) & 0x400:
                raise ValueError("source symlink or reparse point refused")
        if not current.is_file() or sha256(current) != digest:
            raise ValueError(f"source missing or changed: {path}")


def _native_evidence(att, qa):
    """Validate that the frames are rendered from the bound edited PDF, not the original scenes."""
    import fitz

    try:
        meta = json.loads((att / "import.json").read_text(encoding="utf-8"))
        if qa.get("native_edit") != meta or meta.get("preview_source") != "edited_pdf":
            raise ValueError("native metadata mismatch")
        if (meta.get("preview_dpi") != 96 or meta.get("preview_colorspace") != "RGB"
                or meta.get("preview_alpha") is not False or meta.get("structural_validation_passed") is not True):
            raise ValueError("native render or structural check not established")
        parent = meta.get("parent_attempt")
        if (not isinstance(parent, str) or len(parent) != 2 or not parent.isascii() or not parent.isdigit()
                or parent >= att.name or meta.get("parent_native_sha256") != sha256(att.parent / parent / "book.designcraft")):
            raise ValueError("native parent provenance mismatch")
        _source_evidence(att, meta)
        if meta.get("native_sha256") != sha256(att / "book.designcraft") or meta.get("pdf_sha256") != sha256(att / "book.pdf"):
            raise ValueError("native or PDF hash mismatch")
        with fitz.open(att / "book.pdf") as pdf:
            if pdf.page_count < 1 or pdf.page_count != meta.get("pages"):
                raise ValueError("native PDF page count mismatch")
            frames = {p.name: sha256(p) for p in sorted((att / "preview").glob("page-*.png"))}
            if frames != meta.get("preview_sha256") or len(frames) != pdf.page_count:
                raise ValueError("preview list or hash mismatch")
            for index, page in enumerate(pdf):
                name = f"page-{index + 1:02d}.png"
                actual = fitz.Pixmap(str(att / "preview" / name))
                expected = page.get_pixmap(dpi=96, colorspace=fitz.csRGB, alpha=False)
                if (actual.width, actual.height, actual.n, actual.samples) != (expected.width, expected.height, expected.n, expected.samples):
                    raise ValueError(f"preview {name} does not match edited PDF")
        return meta
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        raise ReviewError(f"native edit verification failed: {exc}") from exc


def _confirm_native(rv):
    confirmation = rv.get("native_edit_confirmation")
    if (rv.get("reviewer_mode") != "human" or not isinstance(confirmation, dict)
            or any(confirmation.get(key) is not True for key in NATIVE_CONFIRMATIONS)):
        raise ReviewError("native edits require explicit human confirmation of output, source fidelity and geometry")


def _validate_binding(att, ctx):
    frames = {p.name: sha256(p) for p in sorted((att / "preview").glob("page-*.png"))}
    scenes = {p.name: sha256(p) for p in sorted((att / "scenes").glob("*.json"))}
    if (ctx.get("frames") != frames or ctx.get("scenes") != scenes
            or ctx.get("outputs") != _bound_files(att) or ctx.get("rubric_sha256") != sha256(RUBRIC)):
        raise ReviewError("reviewed files changed or binding is incomplete: bind and review again")


def review_context(out_dir):
    """Bind the latest attempt's frames + scenes + rubric. Returns the context (also written next to the attempt)."""
    out = Path(out_dir)
    att = _attempt_dir(out)
    frames = {p.name: sha256(p) for p in sorted((att / "preview").glob("page-*.png"))}
    if not frames:
        raise ReviewError("attempt has no preview frames (backend without png capability?)")
    scenes = {p.name: sha256(p) for p in sorted((att / "scenes").glob("*.json"))}
    qa_path = att / "qa.json"
    qa = json.loads(qa_path.read_text(encoding="utf-8")) if qa_path.is_file() else {}
    native = _native_evidence(att, qa) if qa.get("native_edit") is not None else None
    ctx = {"attempt": att.name, "frames": frames, "scenes": scenes, "outputs": _bound_files(att), "rubric_sha256": sha256(RUBRIC), "rubric": str(RUBRIC),
           "frame_dir": str(att / "preview"), "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "instructions": "Give every frame + the rubric to a reviewer that did NOT author this attempt. It must return the review JSON with these hashes copied verbatim."}
    if native is not None:
        ctx["native_edit"] = native
    body = json.dumps(ctx, indent=1, sort_keys=True)
    (att / "review-context.json").write_text(body, encoding="utf-8")
    ctx["review_context_sha256"] = sha256(att / "review-context.json")
    return ctx


def record_review(out_dir, review_path):
    """Validate a review against the bindings; store it with the attempt. Raises ReviewError on any mismatch (never a silent pass)."""
    out = Path(out_dir)
    att = _attempt_dir(out)
    ctx_path = att / "review-context.json"
    if not ctx_path.is_file():
        raise ReviewError("run review-context first")
    ctx = json.loads(ctx_path.read_text(encoding="utf-8"))
    rv = json.loads(Path(review_path).read_text(encoding="utf-8"))
    _validate_binding(att, ctx)
    if rv.get("review_context_sha256") != sha256(ctx_path):
        raise ReviewError("review is bound to a different review-context (stale or tampered)")
    if rv.get("reviewer_mode") not in FRESH_MODES:
        raise ReviewError(f"reviewer_mode must be one of {sorted(FRESH_MODES)}: the author of an attempt may not review it")
    if "native_edit" in ctx:
        _native_evidence(att, json.loads((att / "qa.json").read_text(encoding="utf-8")))
        _confirm_native(rv)
    if rv.get("frame_hashes") != ctx["frames"]:
        raise ReviewError("frame_hashes do not match the attempt's previews")
    missing = sorted(set(ctx["frames"]) - set(rv.get("reviewed_frames", [])))
    if missing:
        raise ReviewError(f"frames not reviewed: {missing}")
    scores = rv.get("dimension_scores", {})
    if set(scores) != set(DIMENSIONS) or not all(isinstance(v, (int, float)) and 0 <= v <= 1 for v in scores.values()):
        raise ReviewError(f"dimension_scores must cover exactly {DIMENSIONS} with values in 0..1")
    mean = round(sum(scores.values()) / len(DIMENSIONS), 3)
    blockers = rv.get("blockers", [])
    verdict = "pass" if not blockers and mean >= PASS_MEAN else ("fail" if blockers or mean < 0.5 else "revise")
    if rv.get("verdict") not in (None, verdict):
        raise ReviewError(f"verdict {rv.get('verdict')!r} contradicts the rubric rule (computed {verdict!r}: blockers={len(blockers)}, mean={mean})")
    stored = {**rv, "verdict": verdict, "mean": mean, "attempt": att.name, "recorded": time.strftime("%Y-%m-%dT%H:%M:%S")}
    (att / "review.json").write_text(json.dumps(stored, indent=1, ensure_ascii=False), encoding="utf-8")
    ep = att / "episode.json"
    if ep.is_file():   # the episode package carries the fresh review and any human intervention note
        e = json.loads(ep.read_text(encoding="utf-8"))
        e["verification"]["fresh_review"] = {"verdict": verdict, "mean": mean, "reviewer_mode": rv["reviewer_mode"]}
        if rv.get("intervention"):
            e["interventions"].append({"by": rv["reviewer_mode"], "note": rv["intervention"], "at": stored["recorded"]})
        ep.write_text(json.dumps(e, indent=1, ensure_ascii=False), encoding="utf-8")
    return stored


def finalize(out_dir):
    """Promote the latest attempt to final/ only if blocking gates passed AND a fresh review passed. Otherwise refuse with the reason."""
    out = Path(out_dir)
    att = _attempt_dir(out)
    ctx_path = att / "review-context.json"
    rv_path = att / "review.json"
    if not ctx_path.is_file() or not rv_path.is_file():
        raise ReviewError(f"attempt {att.name} has no recorded fresh review (review-context -> reviewer -> record-review)")
    rv = json.loads(rv_path.read_text(encoding="utf-8"))
    if rv.get("review_context_sha256") != sha256(ctx_path):
        raise ReviewError("review is bound to a different review-context")
    ctx = json.loads(ctx_path.read_text(encoding="utf-8"))
    _validate_binding(att, ctx)
    qa = json.loads((att / "qa.json").read_text(encoding="utf-8"))
    native_attested = False
    if not qa.get("gate_pass"):
        codes = [i.get("code") for i in qa.get("blocking_issues", [])]
        if codes != ["NATIVE_EDIT_UNVERIFIED"] or "native_edit" not in ctx:
            raise ReviewError(f"attempt {att.name} failed blocking gates: {codes}")
        _native_evidence(att, qa)
        _confirm_native(rv)
        native_attested = True
    if rv["verdict"] != "pass":
        raise ReviewError(f"attempt {att.name} review verdict is {rv['verdict']!r} (mean {rv['mean']}, blockers {len(rv.get('blockers', []))})")
    final = out / "final"
    final.mkdir(exist_ok=True)
    import shutil
    for name in ("book.pdf", "book.pptx", "book.designcraft"):
        if (name != "book.designcraft" or native_attested) and (att / name).is_file():
            shutil.copy2(att / name, final / name)
        else:
            (final / name).unlink(missing_ok=True)
    rec = {"attempt": att.name, "review_mean": rv["mean"], "reviewer_mode": rv["reviewer_mode"], "advisory": [i["code"] for i in qa.get("advisory_issues", [])],
           "finalized": time.strftime("%Y-%m-%dT%H:%M:%S"), "reference_basis": qa.get("reference_basis", {}).get("tag")}
    if native_attested:
        rec["native_edit_human_attested"] = True
        rec["native_edit_confirmation"] = {key: rv["native_edit_confirmation"][key] for key in NATIVE_CONFIRMATIONS}
        rec["native_edit_automated_checks"] = {"pdf_preview_binding": "verified", "source_fidelity": "not_verified",
                                               "page_geometry_and_clipping": "not_verified", "scene_parity": "not_verified"}
    (final / "FINAL.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return rec
