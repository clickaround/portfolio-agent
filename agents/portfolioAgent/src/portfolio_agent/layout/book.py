"""Plan -> SceneDocuments (mm). Dispatches each page role to a grid composition (compositions.py / bleed.py) and adds the running furniture.

Composition choice per role: cover; split -> feature; hero -> plate when the asset is a drawing else hero; pair; grid (3+); text; closing.
Page flags from the plan override the role default: `bleed` (full|split|top|grid) -> bleed_*; `strip` (or 5+ graphics on a grid) -> strip;
`dark` inverts paper/ink for that page and lays a full-page `dark-NN` ground under everything.
Variant 1 mirrors / swaps bands so adjacent pages of the same role never repeat (gate REPEATED_LAYOUT).
"""
from portfolio_agent.core.geometry import columns, fit  # noqa: F401  (fit re-exported for callers of this module)
from . import bleed as B
from . import compositions as C
from . import photoset as P
from .typesystem import TypeSystem

GRID_COLUMNS = 12
COMPOSITIONS = {**C.COMPOSITIONS, **B.COMPOSITIONS, **P.COMPOSITIONS}


def pick(page, A):
    role = page["role"]
    k = len(page["assets"])
    bl = page.get("bleed")
    if bl and k:
        if bl == "grid" or k >= 2:
            return "bleed_grid"
        return {"full": "bleed_full", "split": "bleed_split", "top": "bleed_top"}.get(bl, "bleed_full")
    if page.get("photoset"):
        return "photoset"   # host named a photo-set template (layout/photoset.py)
    if role == "grid" and (page.get("strip") or (k >= 5 and not page.get("_index") and not page.get("_diagram_row"))):
        return "strip"
    if role == "grid" and 3 <= k <= 6 and not page.get("_index") and not page.get("_diagram_row") and all(A[a]["role"] != "diagram" for a in page["assets"]):
        return "photoset"   # 3-6 photographs or drawings: a set template chosen by aspect fit (lead + small ones), never a guillotine of equals (blind12 p8)
    if role == "hero" and page["assets"] and A[page["assets"][0]]["role"] == "drawing":
        return "plate"
    if role == "grid" and (page.get("_diagram_row") or (2 <= k <= 4 and all(A[a]["role"] == "diagram" for a in page["assets"]))):
        return "diagram_row"   # a page of diagrams is a sequence (equal cells, numbered captions), never a guillotine grid
    if role == "grid" and page.get("_index"):
        return "index_grid"
    if role == "grid" and k == 2:
        return "pair"
    return role


def build_scene(project_id, page, A, spec, variant, ts=None, total=None):
    ts = ts or TypeSystem(spec, page.get("_tokens", {}), None, page.get("doc_title", ""))
    if page.get("dark"):
        ts = ts.inverted()
    g = columns(spec, GRID_COLUMNS)
    c = C.Ctx(page, A, spec, g, ts, variant)
    COMPOSITIONS[pick(page, A)](c)
    if not page.get("_no_furniture"):
        C.furniture(c, total or page.get("total", 0))
    W, H = spec["width_mm"], spec["height_mm"]
    if page.get("dark"):   # full-page ground (to the bleed) under everything; ts.paper is the inverted paper = the book's ink
        c.el(f"dark-{c.pn:02d}", "shape", [-c.b, -c.b, W + 2 * c.b, H + 2 * c.b], -1, style={"fill": ts.paper})
    return {"schema_version": "0.2.0", "project_id": project_id, "page_id": f"page-{page['page']:02d}", "size_mm": [W, H], "elements": c.els}


def build_book(project_id, plan, manifest, spec, alternate=True, force=None, ts=None):
    A = {a["id"]: a for a in manifest["assets"]}
    scenes, last = [], {}
    ts = ts or TypeSystem(spec, plan.get("tokens", {}), None, plan.get("doc_title", ""))
    for pg in plan["pages"]:
        v = 1 if (spec.get("style", {}) or {}).get("mirror") else 0
        if alternate and last.get(pg["role"]) == v:
            v = 1 - v
        if force and pg["page"] in force:
            v = force[pg["page"]]
        last[pg["role"]] = v
        pg["variant"] = v
        pg["total"] = len(plan["pages"])
        pg["doc_title"] = plan.get("doc_title", "")
        scenes.append(build_scene(project_id, pg, A, spec, v, ts, len(plan["pages"])))
    return scenes
