"""Local backend: PyMuPDF compositor. Implements TextMeasurer + Exporter (pdf, pptx).

PDF assets stay vector (show_pdf_page); PPTX has editable text boxes and pictures (PDF assets rasterized there).
PyMuPDF is AGPL-3.0: user-installed dependency, never bundle it in a redistributed build (ADR-0007).
Imports only `portfolio_agent.core` (layering rule). Design references (ideas only, no code copied): DesignCraft scene->PDF, pagedjs bleed/trim.
"""
import functools
import hashlib
import os
from pathlib import Path
import fitz
from portfolio_agent.core.model.conventions import is_title
from portfolio_agent.core.geometry import PT_PER_MM as MM

FONT_DIRS = [r"C:\Windows\Fonts", os.path.expanduser("~/AppData/Local/Microsoft/Windows/Fonts"), "/usr/share/fonts", "/Library/Fonts", os.path.expanduser("~/Library/Fonts")]
DEFAULT_REGULAR = next((f for f in (r"C:\Windows\Fonts\malgun.ttf", "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc") if os.path.exists(f)), None)
DEFAULT_BOLD = next((f for f in (r"C:\Windows\Fonts\malgunbd.ttf",) if os.path.exists(f)), DEFAULT_REGULAR)


PREVIEW_DPI = 80
FONT_EXTS = (".ttf", ".otf", ".ttc")


@functools.lru_cache(maxsize=256)
def resolve_font(spec):
    """Font file path, or a font file stem looked up in system font dirs. Unknown/invalid -> ValueError (never silently substituted).
    Paths must be local font files (.ttf/.otf/.ttc); UNC/network paths are refused."""
    if not spec:
        return None
    if spec.startswith("\\\\") or spec.startswith("//"):
        raise ValueError(f"network font path refused: {spec!r}")
    if os.path.isfile(spec):
        if os.path.splitext(spec)[1].lower() not in FONT_EXTS:
            raise ValueError(f"not a font file (.ttf/.otf/.ttc): {spec!r}")
        return spec
    want = spec.lower().replace(" ", "").replace("-", "")
    for d in FONT_DIRS:
        for root, _, files in os.walk(d) if os.path.isdir(d) else []:
            for f in files:
                stem, ext = os.path.splitext(f)
                if ext.lower() in FONT_EXTS and stem.lower().replace(" ", "").replace("-", "") == want:
                    return os.path.join(root, f)
    raise ValueError(f"font not found: {spec!r} (give a font file path or an installed font file name)")


def _rgb(hexs):
    h = hexs.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _cropped_bytes(src, crop):
    """PNG/JPEG bytes of the `crop` fraction [fx0, fy0, fx1, fy1] of `src` (the source file itself is never touched)."""
    import io
    from PIL import Image
    with Image.open(src) as im:
        w, h = im.size
        fx0, fy0, fx1, fy1 = crop
        part = im.crop((round(fx0 * w), round(fy0 * h), round(fx1 * w), round(fy1 * h)))
        buf = io.BytesIO()
        if part.mode in ("RGBA", "LA", "P"):
            part.save(buf, "PNG")
        else:
            part.convert("RGB").save(buf, "JPEG", quality=92)
    return buf.getvalue()


_ALIGN = {"left": 0, "center": 1, "right": 2}


class LocalBackend:
    name = "local"
    capabilities = frozenset({"pdf", "pptx", "png"})

    def __init__(self):
        self.style = {"font_body": None, "font_title": None, "text_color": "#1a1a1a", "paper_color": "#ffffff", "accent_color": None}

    # ---- TextMeasurer ----
    def configure(self, style):
        st = style or {}
        self.style["font_body"] = resolve_font(st.get("font_body"))
        self.style["font_title"] = resolve_font(st.get("font_title")) or self.style["font_body"]
        self.style["text_color"] = st.get("text_color", "#1a1a1a")
        self.style["paper_color"] = st.get("paper_color", "#ffffff")
        self.style["accent_color"] = st.get("accent_color")

    def _font(self, page, bold, font=None):
        """PDF font name for this page. `font` (v0.2 style.font) overrides the configured body/title font."""
        path = resolve_font(font) if font else (self.style["font_title"] if bold else self.style["font_body"]) or (DEFAULT_BOLD if bold else DEFAULT_REGULAR)
        if path:
            n = "pa" + hashlib.md5(path.encode("utf-8")).hexdigest()[:8]
            try:
                page.insert_font(fontname=n, fontfile=path)
            except Exception as e:  # noqa: BLE001
                raise ValueError(f"font could not be loaded: {path!r}: {e}") from e
            return n
        return "hebo" if bold else "helv"

    def font_available(self, name):
        try:
            return bool(resolve_font(name))
        except ValueError:
            return False

    def text_fits(self, text, w_mm, h_mm, size_pt, bold=False, style=None):
        st = style or {}
        d = fitz.open()
        p = d.new_page(width=w_mm * MM + 20, height=h_mm * MM + 20)
        rc = p.insert_textbox(fitz.Rect(0, 0, w_mm * MM, h_mm * MM), text or "", fontsize=size_pt, fontname=self._font(p, bold, st.get("font")), align=_ALIGN[st.get("align", "left")], lineheight=st.get("line_height"))
        d.close()
        return rc >= 0

    # ---- Exporter ----
    def export(self, scenes, manifest, project_root, out_base, spec, formats):
        scenes = list(scenes)
        self.configure(spec.get("style"))
        out_base = Path(out_base)
        out_base.parent.mkdir(parents=True, exist_ok=True)
        files, notes, overflow = {}, [], []
        formats = set(formats)
        if "pdf" in formats:
            overflow = self._pdf(scenes, manifest, project_root, str(out_base) + ".pdf", spec)
            files["pdf"] = str(out_base) + ".pdf"
            if "png" in formats:  # review previews of the exact PDF render (what the host agent should LOOK at)
                prev = out_base.parent / "preview"
                prev.mkdir(exist_ok=True)
                d = fitz.open(files["pdf"])
                for i, pg in enumerate(d):
                    pg.get_pixmap(dpi=PREVIEW_DPI).save(str(prev / f"page-{i + 1:02d}.png"))
                files["png"] = str(prev)
                d.close()
        if "pptx" in formats:
            notes += self._pptx(scenes, manifest, project_root, str(out_base) + ".pptx", str(out_base.parent / "_tmp"))
            files["pptx"] = str(out_base) + ".pptx"
        return {"exit": 0, "files": files, "notes": notes, "overflow": overflow}

    def _pdf(self, scenes, manifest, project_root, out_pdf, spec):
        A = {a["id"]: a for a in manifest["assets"]}
        b = spec.get("bleed_mm", 0)
        doc = fitz.open()
        overflow, srcs = [], {}
        txt = _rgb(self.style["text_color"])
        for sc in scenes:
            W, H = sc["size_mm"]
            pg = doc.new_page(width=(W + 2 * b) * MM, height=(H + 2 * b) * MM)
            if self.style["paper_color"].lower() != "#ffffff":
                pg.draw_rect(pg.rect, color=None, fill=_rgb(self.style["paper_color"]))
            for e in sorted(sc["elements"], key=lambda e: e["z_index"]):
                if e.get("visible") is False:
                    continue
                x, y, w, h = e["box_mm"]
                r = fitz.Rect((x + b) * MM, (y + b) * MM, (x + w + b) * MM, (y + h + b) * MM)
                if e["kind"] == "image":
                    src = Path(project_root) / A[e["asset_id"]]["relative_path"]
                    if e.get("crop"):   # bleed cover: only the visible fraction of the source goes into the PDF (gate checked its aspect)
                        pg.insert_image(r, stream=_cropped_bytes(src, e["crop"]), keep_proportion=False)
                    else:
                        pg.insert_image(r, filename=str(src), keep_proportion=False)
                elif e["kind"] in ("pdf-region", "svg"):
                    path = str(Path(project_root) / A[e["asset_id"]]["relative_path"])
                    if path not in srcs:
                        srcs[path] = fitz.open(path) if e["kind"] == "pdf-region" else fitz.open("pdf", fitz.open(path).convert_to_pdf())
                    pg.show_pdf_page(r, srcs[path], 0, keep_proportion=True)
                elif e["kind"] == "shape":
                    st = e.get("style") or {}
                    pg.draw_rect(r, color=None, fill=_rgb(st["fill"]) if st.get("fill") else _rgb(self.style["accent_color"]) if self.style["accent_color"] else txt,
                                 fill_opacity=float(st.get("opacity", 1.0)))
                elif e["kind"] == "text":
                    st = e.get("style") or {}
                    rc = pg.insert_textbox(r, e.get("text", ""), fontsize=e.get("font_size_pt", 10), fontname=self._font(pg, is_title(e["id"]), st.get("font")),
                                           color=_rgb(st["color"]) if st.get("color") else txt, align=_ALIGN[st.get("align", "left")], lineheight=st.get("line_height"))
                    if rc < 0:
                        overflow.append({"page": sc["page_id"], "element": e["id"]})
        doc.set_metadata({"title": spec.get("title", "Portfolio"), "producer": "portfolio-agent local backend"})
        doc.save(out_pdf, garbage=3, deflate=True)
        doc.close()
        for s in srcs.values():
            s.close()
        return overflow

    def _pptx(self, scenes, manifest, project_root, out_pptx, tmp_dir):
        from pptx import Presentation
        from pptx.util import Mm, Pt
        from pptx.enum.shapes import MSO_SHAPE
        from pptx.dml.color import RGBColor
        from pptx.enum.text import PP_ALIGN
        _PPT_ALIGN = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}
        A = {a["id"]: a for a in manifest["assets"]}
        prs = Presentation()
        W, H = scenes[0]["size_mm"]
        prs.slide_width, prs.slide_height = Mm(W), Mm(H)
        Path(tmp_dir).mkdir(parents=True, exist_ok=True)
        notes = []
        for sc in scenes:
            sl = prs.slides.add_slide(prs.slide_layouts[6])
            for e in sorted(sc["elements"], key=lambda e: e["z_index"]):
                if e.get("visible") is False:
                    continue
                x, y, w, h = e["box_mm"]
                if e["kind"] == "text":
                    tb = sl.shapes.add_textbox(Mm(x), Mm(y), Mm(w), Mm(h))
                    tb.text_frame.word_wrap = True
                    tb.text_frame.text = e.get("text", "")
                    tb.name = e["id"]
                    for pa in tb.text_frame.paragraphs:
                        for run in pa.runs:
                            run.font.size = Pt(e.get("font_size_pt", 10))
                            run.font.bold = is_title(e["id"])
                            st = e.get("style") or {}
                            run.font.color.rgb = RGBColor.from_string((st.get("color") or self.style["text_color"]).lstrip("#").upper())
                            if st.get("line_height"):
                                pa.line_spacing = st["line_height"]
                            if st.get("font"):
                                run.font.name = os.path.splitext(os.path.basename(st["font"]))[0]
                                notes.append(f"pptx: font {st['font']!r} set by file stem; PowerPoint substitutes if not installed")
                            if st.get("align"):
                                pa.alignment = _PPT_ALIGN[st["align"]]
                elif e["kind"] == "shape":
                    sh = sl.shapes.add_shape(MSO_SHAPE.RECTANGLE, Mm(x), Mm(y), Mm(w), Mm(h))
                    sh.fill.solid()
                    fill = (e.get("style") or {}).get("fill")
                    sh.fill.fore_color.rgb = RGBColor.from_string((fill or self.style["accent_color"] or self.style["text_color"]).lstrip("#").upper())
                    sh.line.fill.background()
                    sh.name = e["id"]
                else:
                    a = A[e["asset_id"]]
                    src = Path(project_root) / a["relative_path"]
                    if e["kind"] in ("pdf-region", "svg"):
                        png = Path(tmp_dir) / f"{a['id']}.png"
                        d = fitz.open(src) if e["kind"] == "pdf-region" else fitz.open("pdf", fitz.open(src).convert_to_pdf())
                        d[0].get_pixmap(dpi=200).save(png)
                        d.close()
                        src = png
                        notes.append(f"{a['id']}: PDF rasterized at 200dpi in PPTX (vector kept only in PDF)")
                    pic = sl.shapes.add_picture(str(src), Mm(x), Mm(y), Mm(w), Mm(h))
                    pic.name = e["id"]
                    if e.get("crop"):   # editable crop in PowerPoint (the picture keeps the whole source)
                        fx0, fy0, fx1, fy1 = e["crop"]
                        pic.crop_left, pic.crop_right, pic.crop_top, pic.crop_bottom = fx0, 1 - fx1, fy0, 1 - fy1
        prs.save(out_pptx)
        return sorted(set(notes))


BACKEND = LocalBackend()
