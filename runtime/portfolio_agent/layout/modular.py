"""Modular layout: a GRID SYSTEM (columns x flowlines, asymmetric margins) + a SLOT COMPOSITION, both data
(knowledge/patterns/grid-systems.json, compositions.json). Slots are fractions of the grid and snap to columns/flowlines,
so one composition renders on any grid system and any page size; a host can add compositions as JSON.

Rendering is deterministic: images fit their slot aspect-preserving (anchored), text roles map to the page's words
through the type system. Overlap/fit are still judged by the guardrails afterwards, never assumed.
"""
import json
from portfolio_agent.core.geometry import fit
from portfolio_agent.core.paths import PLUGIN_ROOT
from . import compositions as C
from . import treelayout as TL

GRIDS_FILE = PLUGIN_ROOT / "knowledge" / "patterns" / "grid-systems.json"
COMPS_FILE = PLUGIN_ROOT / "knowledge" / "patterns" / "compositions.json"


def grid_systems():
    return {g["id"]: g for g in json.loads(GRIDS_FILE.read_text(encoding="utf-8"))["systems"]}


def compositions():
    """Our hand-written compositions plus any imported sets (knowledge/patterns/compositions-*.json)."""
    out = {c["id"]: c for c in json.loads(COMPS_FILE.read_text(encoding="utf-8"))["compositions"]}
    for extra in sorted(COMPS_FILE.parent.glob("compositions-*.json")):
        for c in json.loads(extra.read_text(encoding="utf-8")).get("compositions", []):
            out.setdefault(c["id"], c)
    return out


def frame(system, spec, page_no=1):
    """Grid system -> absolute frame for this page: margins (inner on the spine side: left on odd pages), column x's, flowline y's."""
    W, H = spec["width_mm"], spec["height_mm"]
    m = system["margins"]
    if m.get("frac"):
        top, bottom, inner, outer = m["top"] * H, m["bottom"] * H, m["inner"] * W, m["outer"] * W
    else:
        top, bottom, inner, outer = m["top"], m["bottom"], m["inner"], m["outer"]
    left, right = (inner, W - outer) if page_no % 2 == 1 else (outer, W - inner)
    n, g = system["columns"], system["gutter_mm"]
    cw = (right - left - g * (n - 1)) / n
    xs = [round(left + i * (cw + g), 2) for i in range(n)]
    rows = system.get("rows", 6)
    return {"left": round(left, 2), "right": round(right, 2), "top": round(top, 2), "bottom": round(H - bottom, 2),
            "grid": {"n": n, "col_w": round(cw, 2), "gutter": g, "x": xs, "margin_box": [left, top, right - left, H - bottom - top]}, "rows": rows}


class ModularCtx(C.Ctx):
    """Ctx on an arbitrary frame (asymmetric margins, any column count) instead of the spec's symmetric margin."""

    def __init__(self, page, assets, spec, fr, ts, variant=0):
        super().__init__(page, assets, spec, fr["grid"], ts, variant)
        self.left, self.right, self.cw = fr["left"], fr["right"], round(fr["right"] - fr["left"], 2)
        self.m = fr["top"]
        self.hang = fr["top"] + self.header_h
        self.bottom = fr["bottom"] - self.footer_h
        self.rows = fr["rows"]

    def snap_cols(self, a, b):
        """fraction range -> (x, w) snapped to column edges."""
        n = self.grid["n"]
        c0, c1 = round(a * n), max(round(a * n) + 1, round(b * n))
        c0, c1 = min(c0, n - 1), min(c1, n)
        x = self.x(c0)
        return x, round(self.x(c1 - 1) + self.grid["col_w"] - x, 2)

    def snap_rows(self, a, b, snap=True):
        """fraction range -> (y, h) between hang and bottom. Images snap to the flowlines; text keeps the exact fraction
        (flowlines are coarse; text slots are designed not to overlap in fraction space)."""
        total = self.bottom - self.hang
        if not snap:
            y = self.hang + a * total
            return round(y, 2), round((b - a) * total - (self.gap * 0.5 if b < 1 else 0), 2)
        step = total / self.rows
        r0, r1 = round(a * self.rows), max(round(a * self.rows) + 1, round(b * self.rows))
        r0, r1 = min(r0, self.rows - 1), min(r1, self.rows)
        y = self.hang + r0 * step
        return round(y, 2), round((r1 - r0) * step - (self.gap if r1 < self.rows else 0), 2)


ROLE_STYLE = {"label": "label", "heading": "heading", "body": "body", "caption": "caption", "caption2": "caption", "statement": "display_small",
              "pull": "pull", "display": "display", "tagline": "caption", "keywords-line": "caption_italic"}


def _text_for(page, role):
    kw = page.get("keywords", [])
    return {"label": None, "heading": page.get("title", ""), "body": page.get("text", "") or page.get("caption", ""), "caption": (page.get("captions") or [page.get("caption", "")])[0] if page.get("captions") or page.get("caption") else "",
            "caption2": (page.get("captions") or ["", ""])[1] if len(page.get("captions") or []) > 1 else "", "statement": page.get("statement", "") or page.get("caption", "") or page.get("title", ""),
            "pull": page.get("caption", "") or page.get("text", ""), "display": page.get("title", ""), "tagline": page.get("tagline", ""), "keywords-line": " / ".join(kw[:5]),
            "keywords": kw}.get(role, "")


def _fit_style(ts, txt, w, h, candidates):
    """First style (largest first) whose estimated area need fits the slot; the last candidate is the floor."""
    for st in candidates:
        if TL.text_need_mm2(txt, ts.pt(st)) * 1.15 <= w * h and ts.line_mm(st) <= h:
            return st
    return candidates[-1]


def render(page, assets, spec, system, comp, ts, variant=0):
    """-> list of elements for one page from a composition + grid system. Extra image slots (no asset) are skipped."""
    fr = frame(system, spec, page.get("page", 1))
    c = ModularCtx(page, assets, spec, fr, ts, variant)
    c.tag(f"modular:{system['id']}:{comp['id']}")
    seen = {}
    for slot in comp["slots"]:
        x, w = c.snap_cols(*slot["col"])
        y, h = c.snap_rows(*slot["row"], snap=(slot["kind"] == "image"))
        if slot["kind"] == "rule":
            c.hairline(f"-{len(c.els)}", x, max(c.hang, y - 1.2), w)
            continue
        if slot["kind"] == "image":
            idx = slot.get("index", 0)
            if idx < len(page["assets"]):
                c.graphic(idx, [x, y, w, h], slot.get("align", "lt"))
            continue
        role = slot["role"]
        if role == "label":
            c.label([x, y, w, min(h, ts.line_mm("label"))])
        elif role == "keywords":
            kws = _text_for(page, "keywords")[:4]
            if kws:
                c.hairline("", x, y, w)
                span = w / max(1, len(kws))
                for k, kwd in enumerate(kws):
                    c.text(f"caption-{k + 1}", [x + k * span, y + 2.0, span - 2, ts.line_mm("label")], f"{k + 1:02d}", "label")
                    c.text(f"caption-{k + 10}", [x + k * span, y + 2.0 + ts.line_mm("label") + 1.0, span - 2, ts.line_mm("subhead")], kwd, "subhead")
        else:
            nth = seen.get(role, 0)
            seen[role] = nth + 1
            if role in ("caption", "caption2"):            # repeated caption slots take the next caption, never the same text twice
                caps = page.get("captions") or ([page.get("caption", "")] if page.get("caption") else [])
                k = nth + (1 if role == "caption2" else 0)
                txt = caps[k] if k < len(caps) else ""
            elif nth and role in ("body", "pull", "statement", "heading", "display"):
                txt = ""                                   # a second body/heading slot stays empty rather than duplicating
            else:
                txt = _text_for(page, role)
            if not txt:
                continue
            st = ROLE_STYLE[role]
            if role in ("statement", "pull", "body"):   # choose the largest style whose text really fits the slot
                st = _fit_style(ts, txt, w, h, {"statement": ("display_small", "pull", "subhead", "caption_italic"), "pull": ("pull", "subhead", "caption_italic"), "body": ("body", "caption")}[role])
            if role in ("caption", "caption2", "label", "tagline", "keywords-line"):
                st = _fit_style(ts, txt, w, h, (st, "label"))
            if TL.text_need_mm2(txt, ts.pt(st)) * 1.1 > w * max(h, ts.line_mm(st)) * 1.6 or h < ts.line_mm(st) * 0.9:
                continue                                   # the slot is too small for this text: leave it empty (gate-clean) instead of overflowing
            h = max(h, ts.line_mm(st))
            name = {"heading": "title", "display": "title", "statement": "title", "body": "body", "pull": "body", "caption": "caption", "caption2": "caption-2", "tagline": "caption-2", "keywords-line": "caption-3"}[role]
            if role in ("display", "statement") and st in ("display", "display_small") and len(txt.split()) >= 2 and len(txt) > 14 and ts.italic_font:
                words = txt.split()
                k = (len(words) + 1) // 2
                lh = ts.line_mm(st)
                c.text(name, [x, y, w, lh], " ".join(words[:k]), st)
                c.text(name + "-2", [x, y + lh, w, lh], " ".join(words[k:]), "display_italic" if st == "display" else "pull")
            else:
                c.text(name, [x, y, w, h], txt, st)
    C.furniture(c, page.get("total", 0))
    return c.els


def suitable(comp, page, assets, spec):
    """Cheap pre-filter: enough image slots for the page's assets, and 'cover'/'closing' tags only on those roles."""
    n_img = sum(1 for s in comp["slots"] if s["kind"] == "image")
    role = page["role"]
    tags = comp.get("tags", [])
    if role == "cover":
        return "cover" in tags and n_img >= len(page["assets"])
    if role == "closing":
        return "closing" in tags
    if "cover" in tags or "closing" in tags:
        return False
    return n_img >= len(page["assets"]) and n_img - len(page["assets"]) <= 1
