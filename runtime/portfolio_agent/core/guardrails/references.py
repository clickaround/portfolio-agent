"""Rights gate for reference cases (cases/RIGHTS_PROTOCOL.md). Pure policy; no layout or backend knowledge.

A case may inform generation only if it is a regular JSON file in cases/approved/, passes the structural checks below,
rights_status == "approved" with recorded permission evidence, use_scope (a list) allows metadata extraction, and it is not heldout.
Anything malformed is REFUSED with a reason (never crashes the run, never slips through).
With zero eligible cases the output must carry NO_EXTERNAL_REFERENCE and make no professional-quality claim.
NOTE: no author consumes approved cases yet (authors/knowledge.py reads synthetic patterns only), so the tag reports availability, not use.
"""
import json
from ..paths import CASES_APPROVED_DIR

NO_REFERENCE = "NO_EXTERNAL_REFERENCE"
AVAILABLE_UNUSED = "APPROVED_CASES_AVAILABLE_NOT_USED"
RETRIEVAL_SCOPE = "extract_metadata"
ALLOWED_SPLITS = (None, "retrieval")  # anything else (heldout, held_out, eval, typos) is refused


def eligibility(case):
    """(ok, reason). Every refusal has a reason so it can be audited."""
    if not isinstance(case, dict):
        return False, "case file root is not a JSON object"
    cid = case.get("case_id")
    if not isinstance(cid, str) or not cid.strip():
        return False, "missing or non-string case_id"
    if case.get("rights_status") != "approved":
        return False, f"rights_status={case.get('rights_status')!r} (only 'approved' qualifies; link_only never does)"
    scope = case.get("use_scope")
    if not isinstance(scope, list) or RETRIEVAL_SCOPE not in scope:
        return False, f"use_scope must be a list containing {RETRIEVAL_SCOPE!r}"
    ev = case.get("rights_evidence")
    if not isinstance(ev, str) or not ev.strip():
        return False, "no rights_evidence (who granted what, when) recorded"
    if case.get("heldout") or case.get("split") not in ALLOWED_SPLITS:
        return False, f"split={case.get('split')!r} heldout={case.get('heldout')!r}: evaluation-only cases are never retrieval references"
    return True, "ok"


def load_cases(directory=None):
    """-> (eligible, refused[{case_id, reason}]). Unreadable, malformed, symlinked or non-.json files are refused, never skipped silently."""
    d = directory or CASES_APPROVED_DIR
    eligible, refused = [], []
    if not d.is_dir():
        return eligible, refused
    for f in sorted(d.iterdir()):
        if f.name.startswith(".") or f.is_dir():
            continue
        if f.is_symlink():
            refused.append({"case_id": f.name, "reason": "symlink refused (could point at heldout or private data)"})
            continue
        if f.suffix != ".json":
            refused.append({"case_id": f.name, "reason": "not a .json case file"})
            continue
        try:
            c = json.loads(f.read_text(encoding="utf-8"))
            ok, why = eligibility(c)
        except Exception as e:  # noqa: BLE001 - any failure must refuse, not crash or pass
            refused.append({"case_id": f.name, "reason": f"unreadable: {type(e).__name__}: {e}"})
            continue
        if ok:
            eligible.append(c)
        else:
            refused.append({"case_id": c.get("case_id", f.name) if isinstance(c, dict) else f.name, "reason": why})
    return eligible, refused


def reference_basis(directory=None):
    """Provenance tag stored in plan.meta and qa.json."""
    eligible, refused = load_cases(directory)
    if not eligible:
        return {"tag": NO_REFERENCE, "approved_cases": 0, "used_in_generation": False, "refused": refused,
                "claim": "synthetic domain guidance only; no professional-quality claim allowed"}
    return {"tag": AVAILABLE_UNUSED, "approved_cases": len(eligible), "case_ids": [c["case_id"] for c in eligible], "used_in_generation": False, "refused": refused,
            "claim": "approved references exist but no author consumes them yet; output is still guidance-only and quality is unverified"}
