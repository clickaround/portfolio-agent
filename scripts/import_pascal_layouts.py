#!/usr/bin/env python3
"""Import pptAgent board layouts (`layout/v1`, agents/pascal-agents/pptAgent/design-system/layouts/*.json, the user's own code)
into our slot-composition data (knowledge/patterns/compositions-pascal.json).

Mapping: pptAgent grid cols/rows -> fractions; slot roles -> ours (headline/title -> heading, label/kicker -> label, chapter -> label,
body -> body, caption -> caption, heading -> heading, drawing/render/photo/diagram -> image slots in reading order);
`decor` rules -> `rule` slots (hairlines). Layouts whose REQUIRED slots cannot be mapped (tables, stats) are skipped and listed.
Usage: import_pascal_layouts.py <layouts_dir> [out.json]
"""
import json
import sys
from pathlib import Path

ROLE_MAP = {"headline": "heading", "title": "heading", "heading": "heading", "label": "label", "kicker": "label", "chapter": "label",
            "body": "body", "caption": "caption", "lead": "body", "subtitle": "pull", "quote": "pull"}
IMAGE_ROLES = {"drawing", "render", "photo", "diagram", "image", "hero"}


def convert(layout):
    g = layout["grid"]
    cols, rows = g["cols"], g["rows"]
    slots, images, skipped = [], 0, []
    for s in layout.get("slots", []):
        x, y, w, h = s["box"]
        col = [round(x / cols, 4), round((x + w) / cols, 4)]
        row = [round(y / rows, 4), round((y + h) / rows, 4)]
        roles = s.get("roles", [])
        if any(r in IMAGE_ROLES for r in roles):
            slots.append({"kind": "image", "index": images, "col": col, "row": row, "align": "lt" if s.get("anchor", "top") == "top" else "lb"})
            images += 1
            continue
        role = next((ROLE_MAP[r] for r in roles if r in ROLE_MAP), None)
        if role is None:
            if not s.get("optional"):
                skipped.append(f"{layout['id']}: required slot {s['name']} roles={roles}")
            continue
        # one heading per page in our model: a second 'heading' slot becomes a pull line
        if role == "heading" and any(t["kind"] == "text" and t["role"] == "heading" for t in slots):
            role = "pull"
        if role == "label" and any(t["kind"] == "text" and t["role"] == "label" for t in slots):
            continue
        slots.append({"kind": "text", "role": role, "col": col, "row": row})
    for d in layout.get("decor", []):
        if d.get("kind") == "rule":
            x, y, w, h = d["box"]
            yy = (y + (h if d.get("edge") == "bottom" else 0)) / rows
            slots.append({"kind": "rule", "col": [round(x / cols, 4), round((x + w) / cols, 4)], "row": [round(yy, 4), round(min(1.0, yy + 0.005), 4)], "color": d.get("color", "line")})
    # our model forbids overlapping boxes (text over image is a different, later feature): skip layouts whose slots overlap
    boxes = [s for s in slots if s["kind"] != "rule"]
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            ox = min(a["col"][1], b["col"][1]) - max(a["col"][0], b["col"][0])
            oy = min(a["row"][1], b["row"][1]) - max(a["row"][0], b["row"][0])
            if ox > 0.01 and oy > 0.01:
                skipped.append(f"{layout['id']}: slots overlap ({a.get('role', 'image')} / {b.get('role', 'image')}) - text-over-image not supported yet")
                return None, skipped
    if skipped or images == 0 and not any(t.get("role") in ("pull", "body") for t in slots):
        return None, skipped
    return {"id": "pascal-" + layout["id"], "images": images, "tags": ["pascal"] + layout.get("intents", []),
            "source": "agents/pascal-agents/pptAgent/design-system/layouts/" + layout["id"] + ".json", "slots": slots}, skipped


def main(src, out):
    comps, skipped = [], []
    for f in sorted(Path(src).glob("*.json")):
        try:
            lay = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if lay.get("contract_version") != "layout/v1":
            continue
        c, sk = convert(lay)
        skipped += sk
        if c:
            comps.append(c)
    data = {"_note": "Imported from the user's pptAgent (pascal-agents) board layouts by scripts/import_pascal_layouts.py; slots are fractions of the source 24x20 grid. Regenerate rather than edit.",
            "compositions": comps, "skipped": skipped}
    Path(out).write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"imported": len(comps), "skipped": len(skipped), "out": out}, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "knowledge/patterns/compositions-pascal.json")
