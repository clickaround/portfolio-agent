"""LayoutAdapter for DesignCraft (Apache-2.0, signed release binary run headless via `designcraft-cli script`).

SceneDocument (mm, canonical) -> DesignCraft command script (points) -> .designcraft (native editable), PDF, PPTX, IDML.
Runs only the pinned/hash-verified binary under .cache/bin/designcraft. No network. Source assets are placed by path (never modified).
"""
import json
import os
import subprocess
from pathlib import Path

PT = 72 / 25.4
ROOT = Path(__file__).resolve().parents[2]  # plugin root (backends/designcraft/adapter.py)
CLI = next(iter((ROOT / ".cache/bin/designcraft").glob("x/*/designcraft-cli.exe")), None) or next(iter((ROOT / ".cache/bin/designcraft").glob("x/*/designcraft-cli")), None)


def _p(path):
    return str(Path(path).resolve()).replace("\\", "/")


# Font file stem (scene v0.2 `style.font`, as the local backend resolves it) -> DesignCraft (family, fontStyle).
# Only installed Windows families are listed; an unknown stem is passed as a family name and DesignCraft substitutes (noted).
FONT_STEMS = {
    "georgia": ("Georgia", "Regular"), "georgiai": ("Georgia", "Italic"), "georgiab": ("Georgia", "Bold"), "georgiaz": ("Georgia", "Bold Italic"),
    "cambria": ("Cambria", "Regular"), "cambriai": ("Cambria", "Italic"), "cambriab": ("Cambria", "Bold"), "cambriaz": ("Cambria", "Bold Italic"),
    "malgun": ("Malgun Gothic", "Regular"), "malgunbd": ("Malgun Gothic", "Bold"), "malgunsl": ("Malgun Gothic", "Semilight"),
    "arial": ("Arial", "Regular"), "arialbd": ("Arial", "Bold"), "ariali": ("Arial", "Italic"), "arialbi": ("Arial", "Bold Italic"),
    "segoeui": ("Segoe UI", "Regular"), "segoeuib": ("Segoe UI", "Bold"), "segoeuii": ("Segoe UI", "Italic"), "times": ("Times New Roman", "Regular"), "timesbd": ("Times New Roman", "Bold"), "timesi": ("Times New Roman", "Italic"),
}
ALIGN = {"left": "left", "center": "center", "right": "right"}


def font_of(spec, default_family, bold):
    """-> (family, fontStyle, known). `spec` is a stem or a file path from element.style.font."""
    if not spec:
        return default_family, ("Bold" if bold else "Regular"), True
    stem = os.path.splitext(os.path.basename(spec))[0].lower()
    if stem in FONT_STEMS:
        return FONT_STEMS[stem] + (True,)
    return spec, "Regular", False


def _rgb255(hexs):
    h = hexs.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]


def build_script(scenes, manifest, project_root, out_base, family="Malgun Gothic", text_color="#1a1a1a"):
    A = {a["id"]: a for a in manifest["assets"]}
    lines, emap, notes = [], {}, []

    def add(cmd, params):
        lines.append(f"{cmd} {json.dumps(params, ensure_ascii=False)}")
        return len(lines) - 1  # step index usable as $N

    W, H = scenes[0]["size_mm"]
    add("file.new", {"width": round(W * PT, 2), "height": round(H * PT, 2), "pages": len(scenes), "intent": "print", "facingPages": False})
    swatches = {}

    def swatch(hexs):
        if hexs not in swatches:
            name = f"pa_{hexs.lstrip('#').lower()}"
            add("swatch.create", {"name": name, "color": _rgb255(hexs)})
            swatches[hexs] = name
        return swatches[hexs]

    styles = {}
    unknown_fonts = set()

    def style_key(e):
        st = e.get("style") or {}
        fam, fstyle, known = font_of(st.get("font"), family, e["id"].startswith("title"))
        if not known:
            unknown_fonts.add(st.get("font"))
        return (round(e.get("font_size_pt", 10), 1), fam, fstyle, st.get("color") or text_color, ALIGN.get(st.get("align", "left"), "left"), float(st.get("line_height", 1.4)))

    for sc in scenes:
        for e in sc["elements"]:
            if e["kind"] == "text" and e.get("text"):
                key = style_key(e)
                if key not in styles:
                    size, fam, fstyle, color, align, lh = key
                    name = f"pa_{len(styles):03d}"
                    styles[key] = name
                    add("style.paragraph.create", {"name": name, "para": {"hyphenate": False, "align": align},
                                                   "chars": {"fontFamily": fam, "fontStyle": fstyle, "size": size, "leading": {"kind": "points", "value": round(size * lh, 2)}, "fill": swatch(color)}})
    for pi, sc in enumerate(scenes):
        for e in sorted(sc["elements"], key=lambda e: e["z_index"]):
            if e.get("visible") is False:
                continue
            x, y, w, h = e["box_mm"]
            rect = [round(x * PT, 2), round(y * PT, 2), round((x + w) * PT, 2), round((y + h) * PT, 2)]
            if e["kind"] in ("image", "pdf-region", "svg"):
                k = add("frame.create", {"spread": pi, "rect": rect, "content": "graphic"})
                add("file.place", {"path": _p(Path(project_root) / A[e["asset_id"]]["relative_path"]), "frame": f"${k}.id"})
                if e.get("crop"):
                    notes.append(f"{e['id']}: bleed crop {e['crop']} not applied in DesignCraft (frame holds the whole source; crop it in the editor)")
            elif e["kind"] == "text" and e.get("text"):
                k = add("frame.create", {"spread": pi, "rect": rect, "content": "text", "text": e["text"]})
                emap[e["id"]] = {"step": k, "page": sc["page_id"], "text": e["text"]}
                add("selection.set", {"ids": [f"${k}.id"]})
                add("style.paragraph.apply", {"name": styles[style_key(e)]})
            elif e["kind"] == "shape":
                fill = (e.get("style") or {}).get("fill") or text_color
                k = add("frame.create", {"spread": pi, "rect": rect, "shape": "rectangle", "content": "unassigned"})
                add("object.fill", {"ids": [f"${k}.id"], "swatch": swatch(fill)})
    base = _p(out_base)
    add("file.exportIdml", {"path": base + ".idml"})
    add("file.exportPptx", {"path": base + ".pptx"})
    if unknown_fonts:
        notes.append(f"designcraft: font(s) {sorted(map(str, unknown_fonts))} not in FONT_STEMS; passed as family names, DesignCraft may substitute")
    return "\n".join(lines) + "\n", emap, notes


def run(scenes, manifest, project_root, out_base, family="Malgun Gothic", text_color="#1a1a1a"):
    if CLI is None:
        raise RuntimeError("BACKEND_NOT_AVAILABLE: designcraft-cli not found under .cache/bin/designcraft (download + verify SHA256 first)")
    out_base = Path(out_base)
    out_base.parent.mkdir(parents=True, exist_ok=True)
    script = out_base.with_suffix(".dcscript")
    text, emap, notes = build_script(scenes, manifest, project_root, out_base, family, text_color)
    script.write_text(text, encoding="utf-8")
    p = subprocess.run([str(CLI), "script", str(script), "--save", _p(out_base) + ".designcraft", "--export", _p(out_base) + ".pdf"], capture_output=True, text=True, timeout=300, encoding="utf-8", errors="replace")
    try:
        res = json.loads(p.stdout[p.stdout.index("{"):])["results"]
        for v in emap.values():
            r = res[v["step"]]
            v["frame"], v["story"] = r.get("id"), r.get("story")
        out_base.with_suffix(".emap.json").write_text(json.dumps(emap, ensure_ascii=False, indent=1), encoding="utf-8")
    except Exception as ex:  # keep going: files may still exist
        emap = {"_error": repr(ex)}
    return {"exit": p.returncode, "stdout_tail": p.stdout[-800:], "stderr_tail": p.stderr[-800:], "notes": notes, "files": {ext: (out_base.with_suffix("." + ext)).is_file() for ext in ("designcraft", "pdf", "idml", "pptx")}}


def edit_text(out_base, element_id, new_text):
    """Replace one text story inside the saved .designcraft, re-export PDF, and PROVE locality: pixels outside the frame and all other pages unchanged."""
    import fitz
    import numpy as np
    out_base = Path(out_base)
    emap = json.loads(out_base.with_suffix(".emap.json").read_text(encoding="utf-8"))
    v = emap[element_id]
    old_pdf, new_pdf = out_base.with_suffix(".pdf"), out_base.with_name(out_base.name + ".edit.pdf")
    n = len(v["text"].encode("utf-8"))
    script = out_base.with_name(out_base.name + ".edit.dcscript")
    params = {"story": v["story"], "start": 0, "end": n, "text": new_text}
    script.write_text("story.replaceRange " + json.dumps(params, ensure_ascii=False) + chr(10), encoding="utf-8")
    p = subprocess.run([str(CLI), "script", str(script), "--in", _p(out_base) + ".designcraft", "--save", _p(out_base) + ".edit.designcraft", "--export", _p(new_pdf)], capture_output=True, text=True, timeout=300, encoding="utf-8", errors="replace")
    if p.returncode != 0 or not new_pdf.exists():
        return {"ok": False, "stderr": (p.stderr or p.stdout)[-300:]}
    a, b = fitz.open(old_pdf), fitz.open(new_pdf)
    changed_pages = []
    for i in range(a.page_count):
        pa, pb = a[i].get_pixmap(dpi=72), b[i].get_pixmap(dpi=72)
        if pa.samples != pb.samples:
            changed_pages.append(i + 1)
    text_ok = any(new_text.split()[0] in pg.get_text() for pg in b)
    a.close()
    b.close()
    return {"ok": True, "pages_changed": changed_pages, "expected_page_index": v["page"], "new_text_in_pdf": text_ok}



def _style_notes(scenes):
    """Scene v0.2 `line_height`/`align`/`color`/`font`/`fill` are mapped; anything else in style is reported, never dropped silently."""
    extra = sorted({k for sc in scenes for e in sc["elements"] for k in (e.get("style") or {}) if k not in ("font", "color", "align", "line_height", "fill")})
    return [f"designcraft: unmapped style keys {extra}"] if extra else []


class DesignCraftBackend:
    """Exporter for the signed DesignCraft release binary. Not a TextMeasurer: gates always measure with the local backend,
    so a text-fit result for DesignCraft output is an approximation (DesignCraft composes with its own text engine)."""

    name = "designcraft"
    capabilities = frozenset({"pdf", "pptx", "native", "idml"})

    def export(self, scenes, manifest, project_root, out_base, spec, formats):
        st = spec.get("style") or {}
        fam = font_of(st.get("font_body"), "Malgun Gothic", False)[0] if st.get("font_body") else st.get("font_family", "Malgun Gothic")
        r = run(list(scenes), manifest, project_root, out_base, fam, st.get("text_color", "#1a1a1a"))
        ext = {"pdf": "pdf", "pptx": "pptx", "native": "designcraft", "idml": "idml"}
        files = {f: (str(Path(out_base)) + "." + ext[f] if r["files"].get(ext[f]) else None) for f in formats if f in ext}
        return {"exit": r["exit"], "files": files, "notes": ([r["stderr_tail"]] if r["stderr_tail"] else []) + r.get("notes", []) + _style_notes(scenes), "overflow": []}

    def edit_text(self, out_base, element_id, new_text):
        return edit_text(out_base, element_id, new_text)


BACKEND = DesignCraftBackend()
