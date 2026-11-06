"""Book-level type system: tokens in -> per-role element `style` dicts out (scene v0.2).

Rules and sources: knowledge/editorial/layout-craft.md §4 and §6
- body 10-12 pt print (Butterick), default 10 pt; user `style.body_pt` wins
- line spacing 120-145 % (Butterick): body 1.35, caption 1.3, display 1.08
- modular scale 1.25 (major third); display = 6 steps above body (~38 pt), heading 2 steps; captions one step below body; labels 1.5 steps below (floor 6.5 pt)
- measure 45-75 characters (Bringhurst) -> `measure_cols()` picks how many grid columns a text column may span
- one display family + one body family, never a third; display serif only if installed AND the text is Latin (CJK falls back to the body family)
Everything here is pure; fonts are only *named* (the backend resolves them). Domain defaults come from the pattern's `tokens` (data), user `spec.style` overrides.
"""
import re

SCALE = 1.25
PT = 0.3528  # mm per pt
DEFAULT_TOKENS = {"paper": "#ffffff", "ink": "#1a1a1a", "accent": "#1f4e5f", "display": "sans"}
SERIF_CANDIDATES = (("georgia", "georgiai"), ("cambria", "cambriai"))
_NON_LATIN = re.compile(r"[ᄀ-￿]")


def latin_only(text):
    return not _NON_LATIN.search(text or "")


def mix(hex_a, hex_b, t):
    """Linear mix of two #rrggbb colours (t = share of b)."""
    ca = [int(hex_a.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    cb = [int(hex_b.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


class TypeSystem:
    def __init__(self, spec, pattern_tokens, measurer, sample_text=""):
        st = spec.get("style", {}) or {}
        tok = {**DEFAULT_TOKENS, **(pattern_tokens or {})}
        self.scale_factor = min(spec["width_mm"], spec["height_mm"]) / 210.0
        self.body_pt = float(st.get("body_pt") or 10.0)
        self.title_scale = float(st.get("title_scale") or 1.0)
        self.paper = st.get("paper_color") or tok["paper"]
        self.ink = st.get("text_color") or tok["ink"]
        self.accent = st.get("accent_color") or tok["accent"]
        self.muted = mix(self.ink, self.paper, 0.45)
        self.hairline = mix(self.ink, self.paper, 0.75)
        self.header = st.get("header", True)
        self.footer = st.get("footer", not self.header)   # header carries title + folio; footer only when asked (or header off)
        avail = getattr(measurer, "font_available", None) or (lambda n: False)
        self.body_font = st.get("font_body")          # None = backend default family
        self.heading_font = st.get("font_title")      # user-chosen heading/display family
        self.italic_font = None
        if not self.heading_font and tok.get("display") == "serif" and latin_only(sample_text):
            for reg, ita in SERIF_CANDIDATES:
                if avail(reg):
                    self.heading_font, self.italic_font = reg, (ita if avail(ita) else None)
                    break
        self.display_serif = bool(self.heading_font and not st.get("font_title"))

    def inverted(self):
        """Same type system on a dark page: paper <-> ink swapped, muted/hairline recomputed (user cases: night/model photos on black)."""
        import copy
        t = copy.copy(self)
        t.paper, t.ink = self.ink, self.paper
        t.muted = mix(t.ink, t.paper, 0.45)
        t.hairline = mix(t.ink, t.paper, 0.75)
        t.accent = mix(self.accent, t.ink, 0.45)   # a dark accent on a dark ground is invisible (blind12 p3): lift it towards the type colour
        return t

    # ---- sizes (pt) ----
    _SIZE_ALIAS = {"display_italic": "display", "caption_italic": "caption", "pull": "subhead_large"}

    def pt(self, role):
        b = self.body_pt
        role = self._SIZE_ALIAS.get(role, role)
        return {"display": b * SCALE ** 6 * self.title_scale, "display_small": b * SCALE ** 5 * self.title_scale, "heading": b * SCALE ** 3 * self.title_scale,
                "subhead": b * SCALE, "subhead_large": b * SCALE ** 2, "body": b, "caption": b / SCALE, "label": max(6.5, b / SCALE ** 1.5), "folio": max(6.5, b / SCALE ** 1.5)}[role]

    def line_mm(self, role, lines=1):
        role = self._SIZE_ALIAS.get(role, role)
        lh = {"display": 1.08, "display_small": 1.1, "heading": 1.2, "subhead": 1.3, "subhead_large": 1.25, "body": 1.35, "caption": 1.3, "label": 1.3, "folio": 1.3}[role]
        # PyMuPDF needs ~0.3 em below the last baseline (measured: 10 pt/1.35 fits from 5.7 mm; formula gives 6.0)
        return round(self.pt(role) * PT * (lh * lines + 0.35), 2)

    # ---- element style dicts (scene v0.2) ----
    def style(self, role, text=""):
        heading_font = self.heading_font if latin_only(text) else self.body_font
        st = {"display": {"font": heading_font, "color": self.ink, "line_height": 1.08},
              "display_small": {"font": heading_font, "color": self.ink, "line_height": 1.1},
              "display_italic": {"font": (self.italic_font or heading_font) if latin_only(text) else self.body_font, "color": self.ink, "line_height": 1.1},
              "heading": {"font": heading_font, "color": self.ink, "line_height": 1.2},
              "subhead": {"font": heading_font, "color": self.ink, "line_height": 1.3},
              "body": {"font": self.body_font, "color": self.ink, "line_height": 1.35},
              "pull": {"font": (self.italic_font or heading_font) if latin_only(text) else self.body_font, "color": self.ink, "line_height": 1.25},
              "caption": {"font": self.body_font, "color": self.muted, "line_height": 1.3},
              "caption_italic": {"font": (self.italic_font or heading_font) if latin_only(text) else self.body_font, "color": self.ink, "line_height": 1.3},
              "label": {"font": self.body_font, "color": self.accent, "line_height": 1.3},
              "folio": {"font": self.body_font, "color": self.muted, "line_height": 1.3}}[role]
        return {k: v for k, v in st.items() if v is not None}

    # ---- measure ----
    def chars_per_mm(self, role, text=""):
        em = self.pt(role) * PT
        return 1.0 / (em * (0.52 if latin_only(text) else 0.95))

    def measure_cols(self, grid, text="", lo=45, hi=72):
        """Smallest column span whose width gives >= `lo` characters at body size, capped at half the grid; never wider than `hi` chars if a narrower span works."""
        cpm = self.chars_per_mm("body", text)
        best = None
        for span in range(1, grid["n"] // 2 + 1):
            w = span * grid["col_w"] + (span - 1) * grid["gutter"]
            if w * cpm >= lo:
                best = span
                break
        return best or grid["n"] // 2

    @staticmethod
    def label_text(s):
        return s.upper() if latin_only(s) else s
