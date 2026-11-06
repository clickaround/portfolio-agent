"""Advisory G4 proxy: lexical grounding of page text against project.md (invented facts surface as TEXT_UNGROUNDED)."""
import re
from pathlib import Path
from ..assets import parse_brief


def _tokens(s):
    return set(re.findall(r"[a-z0-9가-힣]{3,}", (s or "").lower()))


def grounding_issues(scenes, project_root, min_overlap=0.6):
    """ADVISORY G4 proxy: every body/caption/statement sentence must share >= 60 % of its content tokens with project.md
    (AutoDesign uses the same lexical-overlap trick). Catches invented facts; cannot prove truth."""
    try:
        brief = parse_brief(Path(project_root) / "project.md")
    except OSError:
        return []
    corpus = _tokens(brief["title"] + " " + " ".join(brief.get("keywords", [])) + " " + " ".join(brief["sections"].values()) + " " + brief.get("audience", "") + " " + brief.get("domain", ""))
    out = []
    for sc in scenes:
        for e in sc["elements"]:
            # captions describe what the placed asset visibly shows (plan, elevation, scale bar); that evidence is the asset itself,
            # so only body text and titles must be traceable to project.md
            if e["kind"] != "text" or not e.get("text") or not e["id"].startswith(("body-", "title-")):
                continue
            for sent in re.split(r"(?<=[.!?。])\s+", e["text"]):
                toks = _tokens(sent)
                if len(toks) < 4:
                    continue
                ov = len(toks & corpus) / len(toks)
                if ov < min_overlap:
                    out.append({"code": "TEXT_UNGROUNDED", "elements": [e["id"]], "page": sc["page_id"], "details": f"overlap {ov:.2f} < {min_overlap}: {sent[:80]!r}"})
    return out
