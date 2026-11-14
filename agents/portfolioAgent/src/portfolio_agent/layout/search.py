"""Per-page layout search: build every layout the page could take, drop the ones a hard gate rejects, keep the best of the rest.

A page plan fixes WHAT is on the page (role, assets, words). This module only varies HOW it is laid out:
  classic:<v>                 the role's default composition, variant 0/1
  bleed:<full|split|top|grid>:<v>   the bleed devices (layout/bleed.py); they crop, so only for assets marked crop_allowed
  modular:<system>:<comp>:<v> every grid system x slot composition that has room for the page's assets
Each candidate is judged by the page gates (guardrails.gates.qa_scene) and by two content checks of its own (every asset placed,
no words dropped). Survivors are ranked by a geometric score: how much of the page is used, how large the lead graphic is, and how evenly sibling graphics are sized.
The score is geometry only; it says nothing about taste. Every candidate and the reason it was rejected is returned for the record.
"""
from portfolio_agent.core.guardrails import gates
from . import book, modular

GRAPHIC = ("image", "pdf-region", "svg")
BLEEDS = {"full": (1, 1), "split": (1, 1), "top": (1, 1), "grid": (2, 4)}
FIXED = ("bleed", "photoset", "strip", "composition")   # the planner named a device for this page: its choice stands


def option_keys(page, A, spec, systems, comps):
    """Every layout key this page could take, cheapest first. Pages whose plan names a device keep it (classic only)."""
    keys = ["classic:0", "classic:1"]
    if any(page.get(k) for k in FIXED) or page.get("_index") or page.get("_diagram_row"):
        return keys
    k = len(page["assets"])
    if page["role"] not in ("text", "closing") and k and all(A[a].get("crop_allowed") for a in page["assets"]):   # a bleed crops: only where cropping was allowed
        for name, (lo, hi) in BLEEDS.items():
            if lo <= k <= hi:
                keys += [f"bleed:{name}:0", f"bleed:{name}:1"]
    if not page.get("dark"):
        for sid in systems:
            for cid, comp in comps.items():
                if modular.suitable(comp, page, A, spec):
                    keys += [f"modular:{sid}:{cid}:0", f"modular:{sid}:{cid}:1"]
    return keys


def build(key, project_id, page, A, spec, ts, systems, comps):
    """One layout key -> SceneDocument. The page plan is copied, never changed."""
    kind, *rest = key.split(":")
    pg = {k: v for k, v in page.items() if k != "_composition"}
    if kind == "classic":
        return book.build_scene(project_id, pg, A, spec, int(rest[0]), ts, pg.get("total"))
    if kind == "bleed":
        pg["bleed"] = rest[0]
        return book.build_scene(project_id, pg, A, spec, int(rest[1]), ts, pg.get("total"))
    sid, cid, v = rest
    els = modular.render(pg, A, spec, systems[sid], comps[cid], ts, int(v))
    return {"schema_version": "0.2.0", "project_id": project_id, "page_id": f"page-{pg['page']:02d}", "size_mm": [spec["width_mm"], spec["height_mm"]], "elements": els}


def _words(s):
    return len((s or "").split())


def content_issues(scene, page):
    """What the gates cannot see on one page: an asset the layout left out, or body words it silently dropped."""
    out = []
    placed = {e.get("asset_id") for e in scene["elements"]}
    missing = [a for a in page["assets"] if a not in placed]
    if missing:
        out.append({"code": "ASSET_DROPPED", "elements": missing, "details": "the layout has no place for these assets"})
    want = _words(page.get("text"))
    body = " ".join((page.get("text") or "").split())
    have = sum(_words(e["text"]) for e in scene["elements"] if e["kind"] == "text" and e.get("text") and " ".join(e["text"].split()) in body)
    if want and have < want:
        out.append({"code": "TEXT_DROPPED", "elements": [], "details": f"{have} of {want} body words placed"})
    return out


def score(scene, spec):
    """Geometry only, 0..1: share of the page that carries content, weighted with the size of the largest graphic."""
    W, H = scene["size_mm"]
    page_area = W * H

    def area(e):
        x, y, w, h = e["box_mm"]
        x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
        return max(0, x1 - x0) * max(0, y1 - y0)
    graphics = [area(e) for e in scene["elements"] if e["kind"] in GRAPHIC]
    text = sum(area(e) for e in scene["elements"] if e["kind"] == "text" and e.get("text"))
    used = min(1.0, (sum(graphics) + text) / page_area)
    lead = max(graphics, default=0) / page_area
    even = min(graphics) / max(graphics) if len(graphics) > 1 and max(graphics) else 1.0   # a sibling shrunk to a thumbnail reads as an accident
    return {"used": round(used, 3), "lead": round(lead, 3), "even": round(even, 3), "score": round(0.5 * used + 0.3 * lead + 0.2 * even, 3)}


def family(key):
    """A key without its variant: two neighbouring pages of one family read as the same layout."""
    return key.rsplit(":", 1)[0]


def search_page(project_id, page, manifest, spec, measurer, ts, systems, comps, avoid=None):
    """-> (scene, record). record lists every candidate with pass/fail and why; `avoid` is the previous page's family."""
    A = {a["id"]: a for a in manifest["assets"]}
    tried, best = [], None
    for key in option_keys(page, A, spec, systems, comps):
        try:
            scene = build(key, project_id, page, A, spec, ts, systems, comps)
        except Exception as e:   # a composition that cannot take this page is a rejected candidate, not a crash
            tried.append({"layout": key, "ok": False, "why": [f"BUILD_FAILED: {type(e).__name__}"]})
            continue
        issues = [i for i in gates.qa_scene(scene, manifest, spec, measurer) if i["code"] in gates.BLOCKING] + content_issues(scene, page)
        if issues:
            tried.append({"layout": key, "ok": False, "why": sorted({i["code"] for i in issues})})
            continue
        s = score(scene, spec)
        repeat = avoid is not None and family(key) == avoid and page["role"] != "closing"
        rank = s["score"] - (0.5 if repeat else 0.0)
        tried.append({"layout": key, "ok": True, **s, **({"why": ["REPEATS_PREVIOUS_PAGE"]} if repeat else {})})
        if best is None or rank > best[0]:
            best = (rank, key, scene)
    if best is None:
        return None, {"page": page["page"], "chosen": None, "candidates": tried}
    return best[2], {"page": page["page"], "chosen": best[1], "passed": sum(1 for t in tried if t["ok"]), "rejected": sum(1 for t in tried if not t["ok"]), "candidates": tried}


def search_book(project_id, plan, manifest, spec, measurer, ts, scenes, grid_systems=None):
    """Replace each scene by the best passing candidate for its page. A page with no passing candidate keeps its scene.

    Writes the chosen key to the page plan (`layout`, `variant`) so the book gates and a later re-layout see the same page.
    """
    systems = modular.grid_systems()
    if grid_systems:
        systems = {k: v for k, v in systems.items() if k in grid_systems}
    comps = modular.compositions()
    out, report, previous = [], [], None
    for pg, old in zip(plan["pages"], scenes):
        pg.setdefault("total", len(plan["pages"]))
        scene, rec = search_page(project_id, pg, manifest, spec, measurer, ts, systems, comps, avoid=previous)
        if scene is None:
            scene, rec["kept"] = old, "no candidate passed the gates; the author's page is kept"
            previous = None
        else:
            pg["layout"], pg["variant"] = rec["chosen"], int(rec["chosen"].rsplit(":", 1)[1])
            previous = family(rec["chosen"])
        out.append(scene)
        report.append(rec)
    return out, report
