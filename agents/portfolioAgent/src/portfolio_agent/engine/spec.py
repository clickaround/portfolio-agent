"""Output spec defaults and design-plan -> spec translation."""


def default_spec(**kw):
    s = dict(medium="print", width_mm=297, height_mm=210, unit="mm", margin_mm=12, bleed_mm=0, safe_mm=5, gutter_mm=6, page_count=None, style={})
    s.update({k: v for k, v in kw.items() if v is not None})
    return s


def from_design_md(path, palette=None):
    """pptAgent/pascal `DESIGN.md` (google-labs design.md: YAML front matter with colors.*) or `tokens.json` (`palettes.<name>`) -> style.
    Maps primary->text, neutral->paper, tertiary/accent->accent. Fonts are family names; the backend resolves them."""
    import json as _json
    import re as _re
    from pathlib import Path as _P
    p = _P(path)
    st = {}
    if p.suffix == ".json":
        d = _json.loads(p.read_text(encoding="utf-8"))
        pal = d.get("palettes", {})
        name = palette or next(iter(pal), None)
        if name and name in pal:
            c = pal[name]
            st = {"paper_color": c.get("paper"), "text_color": c.get("ink"), "accent_color": c.get("accent")}
        fam = d.get("typography", {}).get("font_family")
        if fam:
            st["font_family"] = fam
    else:
        txt = p.read_text(encoding="utf-8")
        head = txt.split("---")[1] if txt.startswith("---") and txt.count("---") >= 2 else txt
        colors = dict(_re.findall(r"^\s{2}([a-z-]+):\s*'?(#[0-9a-fA-F]{6})'?", head, _re.M))
        st = {"text_color": colors.get("primary"), "paper_color": colors.get("neutral") or colors.get("background"), "accent_color": colors.get("tertiary") or colors.get("accent")}
        m = _re.search(r"fontFamily:\s*([A-Za-z0-9 ]+)", head)
        if m:
            st["font_family"] = m.group(1).strip()
    return {k: v for k, v in st.items() if v}


def from_design_plan(plan):
    """design-plan.json (tokens + composition constraints, see skills/portfolio-design-direction) -> default_spec kwargs. Unknown keys ignored."""
    pal, ty, gr = plan.get("palette", {}), plan.get("type", {}), plan.get("grid", {})
    st = {k: v for k, v in dict(footer=plan.get("footer"), font_title=ty.get("title_font"), font_body=ty.get("body_font"), title_scale=ty.get("title_scale"), body_pt=ty.get("body_pt"),
                                text_color=pal.get("ink"), paper_color=pal.get("paper"), accent_color=pal.get("accent")).items() if v is not None}
    kw = {"style": st}
    if gr.get("margin_mm") is not None:
        kw["margin_mm"] = gr["margin_mm"]
    if gr.get("gutter_mm") is not None:
        kw["gutter_mm"] = gr["gutter_mm"]
    return kw
