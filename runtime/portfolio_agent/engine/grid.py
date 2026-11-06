"""Column grid + aspect-exact boxes for host authors (B4). Removes hand arithmetic, the main source of misaligned images.

Pure computation from the spec and the manifest; no layout decisions. The host still chooses which span each asset uses.
"""
from portfolio_agent.core import assets
from portfolio_agent.core.geometry import columns  # noqa: F401 (shared with the rule-based author)


def span_width(grid, span):
    return round(span * grid["col_w"] + (span - 1) * grid["gutter"], 2)


def asset_boxes(grid, aspect, max_h):
    """For every span 1..n: the aspect-exact box width/height, only when it fits max_h. The host picks one and places it at a column x."""
    out = []
    for s in range(1, grid["n"] + 1):
        w = span_width(grid, s)
        h = round(w / aspect, 2)
        if h <= max_h:
            out.append({"span": s, "w": w, "h": h})
    return out


def view(project_dir, spec, n=12):
    manifest, _ = assets.ingest(project_dir)
    g = columns(spec, n)
    max_h = g["margin_box"][3]
    return {"grid": g,
            "rule": "x of a box = grid.x[start_col]; w = span width below; h = w/aspect (exact). Align tops/bottoms of neighbouring boxes to the same y; use the SAME span for images that should read as a pair.",
            "assets": [{"id": a["id"], "role": a["role"], "aspect": a["aspect"], "boxes_by_span": asset_boxes(g, a["aspect"], max_h)} for a in manifest["assets"]]}
