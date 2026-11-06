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
from pathlib import Path

from portfolio_agent.core.assets import sha256
from portfolio_agent.core.paths import CRITIC_RUBRIC

RUBRIC = CRITIC_RUBRIC
DIMENSIONS = ("hierarchy", "composition_balance", "whitespace_intent", "typography", "sequence_narrative", "asset_fidelity", "domain_fit", "anti_template")
PASS_MEAN = 0.75
FRESH_MODES = {"fresh_subagent", "fresh_session", "human"}


class ReviewError(ValueError):
    pass


def _attempt_dir(out):
    att = sorted((Path(out) / "attempts").glob("[0-9][0-9]"))
    if not att:
        raise ReviewError("no attempts yet: run `compose`/`run` first")
    return att[-1]


def review_context(out_dir):
    """Bind the latest attempt's frames + scenes + rubric. Returns the context (also written next to the attempt)."""
    out = Path(out_dir)
    att = _attempt_dir(out)
    frames = {p.name: sha256(p) for p in sorted((att / "preview").glob("page-*.png"))}
    if not frames:
        raise ReviewError("attempt has no preview frames (backend without png capability?)")
    scenes = {p.name: sha256(p) for p in sorted((att / "scenes").glob("*.json"))}
    ctx = {"attempt": att.name, "frames": frames, "scenes": scenes, "rubric_sha256": sha256(RUBRIC), "rubric": str(RUBRIC),
           "frame_dir": str(att / "preview"), "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "instructions": "Give every frame + the rubric to a reviewer that did NOT author this attempt. It must return the review JSON with these hashes copied verbatim."}
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
    if rv.get("review_context_sha256") != sha256(ctx_path):
        raise ReviewError("review is bound to a different review-context (stale or tampered)")
    if rv.get("reviewer_mode") not in FRESH_MODES:
        raise ReviewError(f"reviewer_mode must be one of {sorted(FRESH_MODES)}: the author of an attempt may not review it")
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
    qa = json.loads((att / "qa.json").read_text(encoding="utf-8"))
    if not qa.get("gate_pass"):
        raise ReviewError(f"attempt {att.name} failed blocking gates: {[i['code'] for i in qa.get('blocking_issues', [])]}")
    rv_path = att / "review.json"
    if not rv_path.is_file():
        raise ReviewError(f"attempt {att.name} has no recorded fresh review (review-context -> reviewer -> record-review)")
    rv = json.loads(rv_path.read_text(encoding="utf-8"))
    if rv["verdict"] != "pass":
        raise ReviewError(f"attempt {att.name} review verdict is {rv['verdict']!r} (mean {rv['mean']}, blockers {len(rv.get('blockers', []))})")
    final = out / "final"
    final.mkdir(exist_ok=True)
    import shutil
    for name in ("book.pdf", "book.pptx"):
        if (att / name).is_file():
            shutil.copy2(att / name, final / name)
    rec = {"attempt": att.name, "review_mean": rv["mean"], "reviewer_mode": rv["reviewer_mode"], "advisory": [i["code"] for i in qa.get("advisory_issues", [])],
           "finalized": time.strftime("%Y-%m-%dT%H:%M:%S"), "reference_basis": qa.get("reference_basis", {}).get("tag")}
    (final / "FINAL.json").write_text(json.dumps(rec, indent=1), encoding="utf-8")
    return rec
