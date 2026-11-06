"""Case/pattern retrieval. Scores domain, keyword overlap and asset-mix fit. Returns rationale (auditable)."""
import json
from portfolio_agent.core.workspace import PATTERNS_FILE
P = json.loads(PATTERNS_FILE.read_text(encoding="utf-8"))["patterns"]

def retrieve(brief, manifest, k=1):
    dom = brief.get("domain", "generic"); kws = {w.lower() for w in brief.get("keywords", [])}
    has_dr = any(a["role"] == "drawing" for a in manifest["assets"]); scored = []
    for p in P:
        s = 10 * (p["domain"] == dom) + 2 * len(kws & set(p["tags"])) + (3 if p["needs_drawing"] == has_dr and p["domain"] == dom else 0) + (1 if p["domain"] == "generic" else 0)
        scored.append((s, p))
    scored.sort(key=lambda x: -x[0])
    return [{"pattern": p, "score": s, "rationale": f"domain={dom} kw_overlap={sorted(kws & set(p['tags']))} drawing_fit={p['needs_drawing'] == has_dr}"} for s, p in scored[:k]]

def baseline_pattern():
    return {"id": "none", "sequence": ["grid"] * 99, "hero_min_ratio": 0.0, "source": "no retrieval"}
