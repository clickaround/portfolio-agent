"""Page DSL v2 (design: project/architecture/P10_LAYOUT_MODEL_DESIGN.md section 4).

What the model reads (problem) and what it writes (layout) are both line formats in grid units of U mm:

  problem                         layout
  page 99 70 m 4 u 3              <id> x y w        one line per element, reading order (top to bottom, left to right)
  0 image 1.600                   ...
  1 title 15.6 7                  end
  2 body 10 412
  3 caption 7.2 38

  image | drawing : aspect ratio (w / h) of the source      title | body | caption | label | text : type size in pt, characters

The layout carries no height. A picture's height follows from its aspect ratio; a text block's height is the smallest one in which
the text fits at its real type size (the product's own measurer). So a layout in this format cannot distort a picture or squeeze
text, which is what the poster-trained weights did on our pages (evidence/P10-postercopilot-proposer.md).

Not in v2 yet: the type step (the model cannot change a type size), crop, layer order (pages here do not stack content).

  page_dsl.py RUN_DIR [--u 1]     per page: problem, layout, and whether the page survives the round trip through the format
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

FURNITURE = ("header", "band-", "hairline-", "dark-", "bleed-", "panel-", "folio", "page-number")
TEXT_KINDS = ("title", "body", "caption", "label")


def kind_of(e):
    if e["kind"] == "text":
        return next((k for k in TEXT_KINDS if e["id"].startswith(k)), "text")
    return "drawing" if e["kind"] == "pdf-region" or e["id"].startswith("drawing") else "image"


def content(sc):
    """The elements a layout places, in a fixed order (pictures first, then text, by id). Furniture stays where the rules put it."""
    els = [e for e in sc["elements"] if e.get("visible") is not False and e["kind"] != "shape" and not e["id"].startswith(FURNITURE)
           and (e["kind"] != "text" or e.get("text"))]
    return sorted(els, key=lambda e: (e["kind"] == "text", e["id"]))


def problem(sc, manifest, spec, u=3):
    A = {a["id"]: a for a in manifest["assets"]}
    W, H = sc["size_mm"]
    lines = [f"page {round(W / u)} {round(H / u)} m {round(spec['margin_mm'] / u)} u {u}"]
    for n, e in enumerate(content(sc)):
        k = kind_of(e)
        if e["kind"] == "text":
            lines.append(f"{n} {k} {e.get('font_size_pt', 10):g} {len(e['text'])}")
        else:
            x, y, w, h = e["box_mm"]
            lines.append(f"{n} {k} {A[e['asset_id']]['aspect'] if e.get('asset_id') in A and not e.get('crop') else w / h:.3f}")
    for x, y, w, h in fixed(sc):   # running header and the like: placed by the rules, the layout must stay clear of them
        lines.append(f"fixed {int(x / u)} {int(y / u)} {-int(-w // u)} {-int(-h // u)}")
    return "\n".join(lines) + "\n"


def fixed(sc):
    """Boxes of visible furniture that carries text (running header, folio). Content may not sit on them."""
    return [e["box_mm"] for e in sc["elements"] if e.get("visible") is not False and e["kind"] == "text" and e.get("text")
            and e["id"].startswith(("header", "folio", "page-number"))]


def encode(sc, u=3):
    rows = []
    for n, e in enumerate(content(sc)):
        x, y, w, h = e["box_mm"]
        gx, gy = round(x / u), round(y / u)
        rows.append((gy, gx, n, max(1, int((x + w) / u + 1e-6) - gx)))
    return "".join(f"{n} {gx} {gy} {gw}\n" for gy, gx, n, gw in sorted(rows)) + "end\n"


def parse(text, n_elements):
    """-> {id: (x, y, w)} or None. Strict: every element once, whole numbers, w >= 1, closed by `end`."""
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    if not lines or lines[-1] != "end" or len(lines) - 1 != n_elements:
        return None
    out = {}
    for ln in lines[:-1]:
        p = ln.split()
        if len(p) != 4 or not all(v.isdigit() for v in p):
            return None
        n, x, y, w = map(int, p)
        if n in out or n >= n_elements or w < 1:
            return None
        out[n] = (x, y, w)
    return out


def text_height(measurer, e, w_mm, max_h):
    """Smallest height (0.5 mm steps) in which the text fits at its type size; None if it does not fit even in max_h."""
    from portfolio_agent.core.model.conventions import is_title
    fits = lambda h: measurer.text_fits(e["text"], w_mm, h, e.get("font_size_pt", 10), is_title(e["id"]), e.get("style"))  # noqa: E731
    if not fits(max_h):
        return None
    lo, hi = 0.0, max_h
    while hi - lo > 0.5:
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if fits(mid) else (mid, hi)
    return round(hi, 2)


def decode(text, sc, manifest, measurer, u=3):
    """Layout text + the page it belongs to -> a new scene with the boxes of the layout, or None if the text is not a layout.
    A text block that fits in no height on the page gets the height of the page (the margin gate then reports it)."""
    els = content(sc)
    boxes = parse(text, len(els))
    if boxes is None:
        return None
    A = {a["id"]: a for a in manifest["assets"]}
    out = copy.deepcopy(sc)
    by_id = {e["id"]: e for e in out["elements"]}
    for n, e in enumerate(els):
        gx, gy, gw = boxes[n]
        x, y, w = gx * u, gy * u, gw * u
        if e["kind"] == "text":
            h = text_height(measurer, e, w, sc["size_mm"][1]) or sc["size_mm"][1]
        else:
            ox, oy, ow, oh = e["box_mm"]
            ar = ow / oh if e.get("crop") or e.get("asset_id") not in A else A[e["asset_id"]]["aspect"]
            h = round(w / ar, 2)
        by_id[e["id"]]["box_mm"] = [x, y, w, h]
    return out


def mirror(text, columns):
    """The same layout mirrored left to right (augmentation)."""
    rows = [tuple(map(int, ln.split())) for ln in text.strip().splitlines()[:-1]]
    return "".join(f"{n} {gx} {gy} {gw}\n" for gy, gx, n, gw in sorted((y, columns - x - w, n, w) for n, x, y, w in rows)) + "end\n"


def layout_hash(problem_text, layout_text):
    """One name per layout whatever the element numbering: page line + sorted (kind, x, y, w). For duplicates and for the split."""
    kinds = {ln.split()[0]: ln.split()[1] for ln in problem_text.strip().splitlines()[1:] if not ln.startswith("fixed")}
    rows = sorted((kinds[ln.split()[0]], *map(int, ln.split()[1:])) for ln in layout_text.strip().splitlines()[:-1])
    key = problem_text.splitlines()[0] + "|" + ";".join(" ".join(map(str, r)) for r in rows)
    return hashlib.blake2b(key.encode(), digest_size=16).hexdigest()


def load_run(run_dir):
    from portfolio_agent.engine import registry
    run_dir = Path(run_dir)
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    scenes = [json.loads(f.read_text(encoding="utf-8")) for f in sorted((run_dir / "scenes").glob("page-*.json"))]
    measurer = registry.get_backend(run.get("backend", "local"))
    measurer.configure(run["spec"].get("style"))
    return run["spec"], manifest, scenes, measurer


def main():
    from portfolio_agent.core.guardrails import gates
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--u", type=int, default=1)
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()
    spec, manifest, scenes, measurer = load_run(a.run)
    ok = 0
    for sc in scenes:
        p, d = problem(sc, manifest, spec, a.u), encode(sc, a.u)
        before = {i["code"] for i in gates.split(gates.qa_scene(sc, manifest, spec, measurer))[0]}
        back = decode(d, sc, manifest, measurer, a.u)
        after = sorted({i["code"] for i in gates.split(gates.qa_scene(back, manifest, spec, measurer))[0]} - before)
        ok += not after
        print(sc["page_id"], f"{len(p) + len(d)} chars", layout_hash(p, d)[:8], "round trip:", "ok" if not after else after)
        if a.show:
            print(p + d)
    print(f"{ok}/{len(scenes)} pages keep their gates through the format (u = {a.u} mm)")


if __name__ == "__main__":
    main()
