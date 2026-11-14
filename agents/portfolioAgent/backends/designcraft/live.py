"""Edit a saved .designcraft document in place, by element key, through a small set of typed operations.

Why this shape (papers read 2026-11-14, DOC_REPORTED):
 - APEX (arXiv 2601.04794): element ids + a few typed tools beat free scripts (34 % of free scripts failed to run); each call is
   run on its own so one failure does not cancel the rest.
 - Talk-to-Your-Slides (arXiv 2505.11604): give the model object data, not screenshots.
 - ACE (arXiv 2608.24103): stable ids shared by the original and the edited state; diff of the two states drives the check.

Every object the exporter creates is named `<page_id>/<element_id>` (adapter.build_script). An object without such a name was made
by the user in the editor; it is reported with the key `user:<designcraft id>` and can be read but is never a target here.
Units: mm outside, points inside DesignCraft. Nothing here judges an edit: engine/live.py does that.
"""
import json
import subprocess
import tempfile
from pathlib import Path

PT = 72 / 25.4


def _cli():
    """The pinned binary, from the adapter beside this file (one place decides which binary runs)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("pa_backend_designcraft_adapter", Path(__file__).with_name("adapter.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.CLI


def _p(path):
    return str(Path(path).resolve()).replace("\\", "/")


def _run(lines, dc_in, save=None, export=None):
    """Run command lines on `dc_in`, every step on its own (--keep-going). -> list of results; a failed step is {"error": ...}."""
    cli = _cli()
    if cli is None:
        raise RuntimeError("BACKEND_NOT_AVAILABLE: designcraft-cli not found under .cache/bin/designcraft")
    with tempfile.TemporaryDirectory() as t:
        script = Path(t) / "live.dcscript"
        script.write_text("\n".join(lines) + "\n", encoding="utf-8")
        cmd = [str(cli), "script", str(script), "--in", _p(dc_in), "--keep-going"]
        if save:
            cmd += ["--save", _p(save)]
        if export:
            cmd += ["--export", _p(export)]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=300, encoding="utf-8", errors="replace")
    try:
        return json.loads(p.stdout[p.stdout.index("{"):])["results"]
    except ValueError:
        raise RuntimeError("DESIGNCRAFT_FAILED: " + (p.stderr or p.stdout)[-400:])


def _line(cmd, params):
    return f"{cmd} {json.dumps(params, ensure_ascii=False)}"


def _mm(v):
    return round(v / PT, 2)


def read(dc):
    """-> {"pages": [{"index", "size_mm", "items": [{key, dc_id, kind, box_mm, text?, overset?, story?, asset?, hidden, locked}]}]}.
    Items are in DesignCraft's own order for the spread."""
    ins = _run(["document.inspect {}"], dc)[0]
    frames = [it for s in ins["spreads"] for it in s["items"] if it.get("story") is not None]
    texts = _run([_line("story.get", {"frame": it["id"]}) for it in frames], dc) if frames else []
    by_frame = {it["id"]: t for it, t in zip(frames, texts) if isinstance(t, dict) and "error" not in t}
    pages = []
    for s in ins["spreads"]:
        x0, y0, x1, y1 = s["pages"][0]["bounds"]
        items = []
        for it in s["items"]:
            a, b, c, d = it["bounds"]
            kind = {"<image>": "image", "<text frame>": "text"}.get(it["kind"], "shape")
            row = {"key": it.get("name") or f"user:{it['id']}", "dc_id": it["id"], "kind": kind, "box_mm": [_mm(a - x0), _mm(b - y0), _mm(c - a), _mm(d - b)],
                   "hidden": bool(it.get("hidden")), "locked": bool(it.get("locked"))}
            if it.get("asset") is not None:
                row["asset"] = it["asset"]
            if it["id"] in by_frame:
                t = by_frame[it["id"]]
                row.update(text=t.get("text", ""), story=t.get("id"), overset=bool(t.get("overset")))
            items.append(row)
        pages.append({"index": s["index"], "size_mm": [_mm(x1 - x0), _mm(y1 - y0)], "origin_pt": [x0, y0], "items": items})
    return {"pages": pages}


def index(doc):
    """key -> (page index, item)."""
    return {it["key"]: (pg["index"], it) for pg in doc["pages"] for it in pg["items"]}


def hit(doc, page_index, x_mm, y_mm):
    """Keys of the items under a point on a page, smallest box first: a mark on a caption inside a large picture means the caption."""
    inside = [it for it in doc["pages"][page_index]["items"] if not it["hidden"]
              and it["box_mm"][0] <= x_mm <= it["box_mm"][0] + it["box_mm"][2] and it["box_mm"][1] <= y_mm <= it["box_mm"][1] + it["box_mm"][3]]
    return [it["key"] for it in sorted(inside, key=lambda it: it["box_mm"][2] * it["box_mm"][3])]


def nearest(doc, page_index, x_mm, y_mm, n=3):
    """Keys of the n items closest to a point (distance to the box, 0 inside). A mark in empty space still means something nearby."""
    def dist(it):
        x, y, w, h = it["box_mm"]
        dx, dy = max(x - x_mm, 0, x_mm - x - w), max(y - y_mm, 0, y_mm - y - h)
        return (dx * dx + dy * dy) ** 0.5
    return [it["key"] for it in sorted((it for it in doc["pages"][page_index]["items"] if not it["hidden"]), key=dist)[:n]]


# ---- typed operations: name -> (required arguments, builder(item, op) -> command lines) ----
def _op_move(it, op):
    return [_line("transform.move", {"dx": round(op["dx_mm"] * PT, 2), "dy": round(op["dy_mm"] * PT, 2), "ids": [it["dc_id"]]})]


def _op_set_box(it, op):
    x, y, w, h = op["box_mm"]
    if w <= 0 or h <= 0:
        raise ValueError("box_mm width and height must be positive")
    ox, oy = it["_origin"]
    lines = [_line("transform.set", {"ids": [it["dc_id"]], "x": round(x * PT + ox, 2), "y": round(y * PT + oy, 2), "width": round(w * PT, 2), "height": round(h * PT, 2), "ref": 0})]
    if it["kind"] == "image":   # the frame changed shape: the picture is re-fitted whole, never stretched
        lines.append(_line("object.fit", {"mode": op.get("fit", "fitProportionally"), "ids": [it["dc_id"]]}))
    return lines


def _op_set_text(it, op):
    if it["kind"] != "text":
        raise ValueError("set_text needs a text element")
    return [_line("story.setText", {"story": it["story"], "text": op["text"]})]


def _op_replace_image(it, op):
    if it["kind"] != "image":
        raise ValueError("replace_image needs an image element")
    if not Path(op["path"]).is_file():
        raise ValueError(f"no such file: {op['path']}")
    return [_line("file.place", {"path": _p(op["path"]), "frame": it["dc_id"]}), _line("object.fit", {"mode": op.get("fit", "fitProportionally"), "ids": [it["dc_id"]]})]


def _op_fit(it, op):
    if op["mode"] not in ("fillProportionally", "fitProportionally", "centerContent"):
        raise ValueError("fit mode must keep the aspect ratio: fillProportionally | fitProportionally | centerContent")
    return [_line("object.fit", {"mode": op["mode"], "ids": [it["dc_id"]]})]


def _op_order(it, op):
    cmd = {"front": "object.bringToFront", "back": "object.sendToBack"}[op["to"]]
    return [_line("selection.set", {"ids": [it["dc_id"]]}), f"{cmd} {{}}"]


def _op_text_style(it, op):
    if it["kind"] != "text":
        raise ValueError("text_style needs a text element")
    attrs = {k: op[k] for k in ("size", "fontFamily", "fontStyle", "tracking") if k in op}
    lines = [_line("selection.set", {"ids": [it["dc_id"]]})]
    if attrs:
        lines.append(_line("type.char", {"attrs": attrs}))
    if "align" in op:
        lines.append(_line("type.align", {"align": op["align"]}))
    if len(lines) == 1:
        raise ValueError("text_style needs one of size, fontFamily, fontStyle, tracking, align")
    return lines


def _op_hide(it, op):
    return [_line("object.setFlags", {"ids": [it["dc_id"]], "hidden": bool(op.get("hidden", True))})]


def _op_delete(it, op):
    return [_line("edit.clear", {"ids": [it["dc_id"]]})]


OPS = {
    "move": (("dx_mm", "dy_mm"), _op_move),
    "set_box": (("box_mm",), _op_set_box),
    "set_text": (("text",), _op_set_text),
    "replace_image": (("path",), _op_replace_image),
    "fit": (("mode",), _op_fit),
    "order": (("to",), _op_order),
    "text_style": ((), _op_text_style),
    "hide": ((), _op_hide),
    "delete": ((), _op_delete),
}

TOOLS = {   # what an LLM host is told; the whole tool surface in one screen
    "move": "{target, dx_mm, dy_mm} shift an element",
    "set_box": "{target, box_mm: [x, y, w, h]} place and size an element; a picture is re-fitted whole",
    "set_text": "{target, text} replace the text of a text element",
    "replace_image": "{target, path} put another source file into a picture frame",
    "fit": "{target, mode: fitProportionally | fillProportionally | centerContent} how a picture sits in its frame (fill crops)",
    "order": "{target, to: front | back} stacking order",
    "text_style": "{target, size?, fontFamily?, fontStyle?, tracking?, align?} type attributes of a text element",
    "hide": "{target, hidden?: bool} hide or show",
    "delete": "{target} remove the element",
}


def apply(dc_in, ops, dc_out, pdf_out=None):
    """Run typed ops on `dc_in`, save `dc_out`. An op that is malformed or fails does not stop the others.
    -> {"results": [{op, target, ok, error?}], "before": doc, "after": doc}"""
    before = read(dc_in)
    origin = {pg["index"]: pg["origin_pt"] for pg in before["pages"]}
    idx = index(before)
    lines, spans, results = [], [], []
    for op in ops:
        r = {"op": op.get("op"), "target": op.get("target"), "ok": False}
        results.append(r)
        try:
            if op.get("op") not in OPS:
                raise ValueError(f"unknown op; known: {sorted(OPS)}")
            if op.get("target") not in idx or str(op.get("target")).startswith("user:"):
                raise ValueError("unknown target" if op.get("target") not in idx else "user-made object: not an agent target")
            need, build = OPS[op["op"]]
            miss = [k for k in need if k not in op]
            if miss:
                raise ValueError(f"missing {miss}")
            page, it = idx[op["target"]]
            if it["locked"]:
                raise ValueError("locked in the editor")
            new = build({**it, "_origin": origin[page]}, op)
        except (ValueError, KeyError, TypeError) as ex:
            r["error"] = str(ex)
            spans.append(None)
            continue
        spans.append((len(lines), len(lines) + len(new)))
        lines += new
    out = _run(lines or ["document.history {}"], dc_in, save=dc_out, export=pdf_out)
    for r, span in zip(results, spans):
        if span is None:
            continue
        errs = [x["error"] for x in out[span[0]:span[1]] if isinstance(x, dict) and "error" in x]
        r["ok"] = not errs
        if errs:
            r["error"] = errs[0]
    return {"results": results, "before": before, "after": read(dc_out)}


def changed(before, after):
    """key -> sorted list of what differs between two reads: box, text, asset, hidden, page, added, removed."""
    a, b = index(before), index(after)
    out = {}
    for k in a.keys() | b.keys():
        if k not in b:
            out[k] = ["removed"]
        elif k not in a:
            out[k] = ["added"]
        else:
            (pa, x), (pb, y) = a[k], b[k]
            f = [name for name in ("text", "asset", "hidden") if x.get(name) != y.get(name)]
            if any(abs(p - q) > 0.05 for p, q in zip(x["box_mm"], y["box_mm"])):
                f.append("box")
            if pa != pb:
                f.append("page")
            if f:
                out[k] = sorted(f)
    return out
