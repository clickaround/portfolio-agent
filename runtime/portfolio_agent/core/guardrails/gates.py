"""Hard-gate QA. Reuses scripts/check_layout.py (geometry) and adds asset/aspect/margin/text/book/PDF checks.

Furniture and bleed elements have their own rules instead of the generic overlap/margin model:
  band-*      cover/spine band in the margin; may not sit under content
  hairline-*  rules; exempt from overlap
  dark-*      full-page ground of a dark page (z -1); exempt
  bleed-*     a graphic that may run to the bleed box and sit under a panel; never under another graphic
  panel-*     solid panel over a bleed graphic; text may sit on a bleed graphic ONLY inside a panel (TEXT_OVER_IMAGE otherwise)
"""
from pathlib import Path
import fitz
from ..assets import sha256
from ..conventions import is_title
from ..legacy_checks import CL, CED  # noqa: F401  (CED re-exported for repair/edit)
from .policy import BLOCKING, ADVISORY, MIN_PT, DRAWING_MIN_FRAC, split  # noqa: F401  (re-exported)
from .grounding import grounding_issues  # noqa: F401  (re-exported)

SPECIAL = ("band-", "hairline-", "dark-", "bleed-", "panel-")
MARGIN_EXEMPT = ("band-", "dark-", "bleed-")


def _ov(a, b):
    x, y, w, h = a["box_mm"]
    x2, y2, w2, h2 = b["box_mm"]
    return min(x + w, x2 + w2) - max(x, x2) > 1e-6 and min(y + h, y2 + h2) - max(y, y2) > 1e-6


def _inside(a, b):
    x, y, w, h = a["box_mm"]
    x2, y2, w2, h2 = b["box_mm"]
    return x >= x2 - 1e-6 and y >= y2 - 1e-6 and x + w <= x2 + w2 + 1e-6 and y + h <= y2 + h2 + 1e-6


def _bleed_issues(sc, spec):
    """Overlap/extent rules for bleed-*, panel-*, dark-* elements (the generic checker never sees them)."""
    W, H = sc["size_mm"]
    b = float(spec.get("bleed_mm", 0) or 0)
    out = []
    els = sc["elements"]
    bleeds = [e for e in els if e["id"].startswith("bleed-")]
    panels = [e for e in els if e["id"].startswith("panel-")]
    plain = [e for e in els if not e["id"].startswith(SPECIAL)]
    for e in bleeds + [e for e in els if e["id"].startswith("dark-")]:
        x, y, w, h = e["box_mm"]
        if x < -b - 1e-6 or y < -b - 1e-6 or x + w > W + b + 1e-6 or y + h > H + b + 1e-6:
            out.append({"code": "OUTSIDE_MARGIN", "elements": [e["id"]], "details": f"beyond the bleed box (bleed {b} mm): {e['box_mm']}"})
    for i, a in enumerate(bleeds):
        for c in bleeds[i + 1:]:
            if _ov(a, c):
                out.append({"code": "BBOX_OVERLAP", "elements": [a["id"], c["id"]], "details": "bleed graphics overlap"})
    for o in plain:
        for e in bleeds:
            if not _ov(o, e):
                continue
            if o["kind"] == "text":
                if not any(_inside(o, p) for p in panels):
                    out.append({"code": "TEXT_OVER_IMAGE", "elements": [o["id"], e["id"]], "details": "text on a bleed graphic must sit inside a panel-* shape"})
            else:
                out.append({"code": "BBOX_OVERLAP", "elements": [o["id"], e["id"]], "details": "element over a bleed graphic"})
    for p in panels:
        for o in plain:
            if o["kind"] != "text" and _ov(o, p):
                out.append({"code": "BBOX_OVERLAP", "elements": [o["id"], p["id"]], "details": "graphic over a panel"})
    return out


def qa_scene(sc, manifest, spec, measurer):
    A = {a["id"]: a for a in manifest["assets"]}
    m = spec["margin_mm"]
    issues = list(CL.check_scene({**sc, "elements": [e for e in sc["elements"] if not e["id"].startswith(SPECIAL)]}, set(A)))
    issues += _bleed_issues(sc, spec)
    for e in sc["elements"]:
        if e["id"].startswith("band-") and (e["box_mm"][2] > m + 1e-6 and e["box_mm"][3] > m + 1e-6):
            issues.append({"code": "BBOX_OVERLAP", "elements": [e["id"]], "details": "background band wider than the margin would sit under content"})
    W, H = sc["size_mm"]
    for e in sc["elements"]:
        x, y, w, h = e["box_mm"]
        if (x < m - 1e-6 or y < m - 1e-6 or x + w > W - m + 1e-6 or y + h > H - m + 1e-6) and not e["id"].startswith(MARGIN_EXEMPT):
            issues.append({"code": "OUTSIDE_MARGIN", "elements": [e["id"]], "details": str(e["box_mm"])})
        if e["kind"] in ("image", "pdf-region", "svg") and e.get("asset_id") in A:
            ar = A[e["asset_id"]]["aspect"]
            if e.get("crop"):   # visible fraction of the source (bleed cover): the box must match the CROPPED aspect
                fx0, fy0, fx1, fy1 = e["crop"]
                if not (0 <= fx0 < fx1 <= 1 and 0 <= fy0 < fy1 <= 1) or e["kind"] != "image":
                    issues.append({"code": "ASPECT_DISTORTION", "elements": [e["id"]], "details": f"bad crop {e['crop']} (raster images only, fractions 0..1)"})
                    continue
                ar = ar * (fx1 - fx0) / (fy1 - fy0)
            if abs((w / h) / ar - 1) > 0.01:
                issues.append({"code": "ASPECT_DISTORTION", "elements": [e["id"]], "details": f"box {w / h:.3f} vs asset {ar:.3f}"})
        if e["id"].startswith("drawing-") and e.get("asset_id") in A and not sc.get("index_page"):
            ca = (W - 2 * m) * (H - 2 * m)
            if w * h / ca < DRAWING_MIN_FRAC and len([x for x in sc["elements"] if x["id"].startswith("drawing-")]) <= 4:   # 5+ = an index/strip, exempt
                issues.append({"code": "DRAWING_SMALL", "elements": [e["id"]], "details": f"drawing fills {w * h / ca:.0%} of the content area (< {DRAWING_MIN_FRAC:.0%}): a thumbnail - give it its own page or a pair"})
        if e["kind"] == "text" and e.get("text") and not measurer.text_fits(e["text"], w, h, e.get("font_size_pt", 10), is_title(e["id"]), e.get("style")):
            issues.append({"code": "TEXT_OVERFLOW", "elements": [e["id"]], "details": f"{e.get('font_size_pt')}pt in {w:.0f}x{h:.0f}mm"})
        if e["kind"] == "text" and e.get("text"):
            floor = MIN_PT["body"] if e["id"].startswith(("body-", "title-")) else MIN_PT["small"]
            if e.get("font_size_pt", 10) < floor - 1e-6:
                issues.append({"code": "TYPE_TOO_SMALL", "elements": [e["id"]], "details": f"{e.get('font_size_pt')}pt < {floor}pt floor"})
    return issues


def qa_book(scenes, manifest, plan, spec, project_root, measurer):
    issues = []
    A = {a["id"]: a for a in manifest["assets"]}
    for sc in scenes:
        for i in qa_scene(sc, manifest, spec, measurer):
            i["page"] = sc["page_id"]
            issues.append(i)
    placed = {e["asset_id"] for sc in scenes for e in sc["elements"] if e.get("asset_id")}
    for aid in sorted(set(A) - placed):
        issues.append({"code": "MISSING_ASSET_ON_PAGE", "elements": [aid], "details": "asset never placed", "page": None})
    for a in A.values():
        if sha256(Path(project_root) / a["relative_path"]) != a["sha256"]:
            issues.append({"code": "SOURCE_MODIFIED", "elements": [a["id"]], "details": "hash mismatch", "page": None})
    sig = [(pg["role"], pg.get("variant", 0)) for pg in plan["pages"]]
    host_authored = all(pg["role"] == "host" for pg in plan["pages"]) if plan["pages"] else False
    for i in range(1, len(sig)):
        if sig[i] == sig[i - 1] and sig[i][0] not in ("closing", "host") and not host_authored:
            issues.append({"code": "REPEATED_LAYOUT", "elements": [], "details": f"pages {i}-{i + 1} {sig[i]}", "page": f"page-{i + 1:02d}"})
    W, H = spec["width_mm"], spec["height_mm"]
    ca = (W - 2 * spec["margin_mm"]) * (H - 2 * spec["margin_mm"])
    best = max((e["box_mm"][2] * e["box_mm"][3] / ca for sc in scenes for e in sc["elements"] if e["kind"] != "text"), default=0)
    if best < plan["hero_min_ratio"]:
        issues.append({"code": "HERO_TOO_SMALL", "elements": [], "details": f"largest graphic {best:.2f} < {plan['hero_min_ratio']}", "page": None})
    return issues


def qa_pdf(pdf, scenes, spec):
    issues = []
    d = fitz.open(pdf)
    b = spec.get("bleed_mm", 0)
    if d.page_count != len(scenes):
        issues.append({"code": "PDF_PAGE_COUNT", "details": f"{d.page_count} != {len(scenes)}"})
    for i, (pg, sc) in enumerate(zip(d, scenes)):
        ew, eh = (sc["size_mm"][0] + 2 * b) * 72 / 25.4, (sc["size_mm"][1] + 2 * b) * 72 / 25.4
        if abs(pg.rect.width - ew) > 0.5 or abs(pg.rect.height - eh) > 0.5:
            issues.append({"code": "PDF_PAGE_SIZE", "details": f"p{i + 1} {pg.rect.width:.1f}x{pg.rect.height:.1f} vs {ew:.1f}x{eh:.1f}"})
        txt = pg.get_text()
        for e in sc["elements"]:
            if e["kind"] == "text" and e.get("text") and e["text"].split()[0] not in txt:
                issues.append({"code": "PDF_TEXT_NOT_EXTRACTABLE", "elements": [e["id"]], "details": f"p{i + 1}"})
            if e["kind"] in ("pdf-region", "svg") and len(pg.get_drawings()) < 5:
                issues.append({"code": "PDF_VECTOR_LOST", "elements": [e["id"]], "details": f"p{i + 1} drawings={len(pg.get_drawings())}"})
        if len(pg.get_images()) < sum(1 for e in sc["elements"] if e["kind"] == "image"):
            issues.append({"code": "PDF_IMAGE_MISSING", "details": f"p{i + 1}"})
    d.close()
    return issues
