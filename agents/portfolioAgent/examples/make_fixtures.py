#!/usr/bin/env python3
"""Generate SYNTHETIC architecture projects (images + vector plan PDF + project.md). No real work/rights involved."""
import sys, random
from pathlib import Path
from PIL import Image, ImageDraw
from reportlab.pdfgen import canvas
OUT = Path(__file__).resolve().parent / "synthetic_projects"

def img(path, w, h, seed, label, tight=False):
    """SYNTHETIC architecture-like image: elevation render, massing model, or section linework (rotates by seed)."""
    r = random.Random(seed); kind = seed % 3; im = Image.new("RGB", (w, h)); d = ImageDraw.Draw(im)
    if kind == 0:  # elevation render: sky gradient, ground, facade with window grid, timber roof, trees
        for y in range(h): c = int(235 - 60 * y / h); d.line([(0, y), (w, y)], fill=(c - 25, c - 5, c + 15))
        gy = int(h * 0.78); d.rectangle([0, gy, w, h], fill=(96, 104, 92)); bx0, bx1, by0 = int(w * .12), int(w * .88), int(h * .32)
        d.rectangle([bx0, by0, bx1, gy], fill=(214, 208, 196)); d.polygon([(bx0 - 20, by0), (bx1 + 20, by0), (bx1, by0 - int(h * .08)), (bx0, by0 - int(h * .08))], fill=(150, 105, 70))
        cols, rows = max(3, w // 160), max(2, (gy - by0) // 140)
        for a in range(cols):
            for b in range(rows):
                x = bx0 + 30 + a * (bx1 - bx0 - 60) // cols; y = by0 + 30 + b * (gy - by0 - 50) // rows; d.rectangle([x, y, x + (bx1 - bx0 - 60) // cols - 24, y + (gy - by0 - 50) // rows - 24], fill=(70 + r.randint(0, 40), 95 + r.randint(0, 40), 115 + r.randint(0, 40)))
        for _ in range(5): tx = r.randint(0, w); d.ellipse([tx - 50, gy - 120, tx + 50, gy - 10], fill=(60, 92 + r.randint(0, 30), 60))
    elif kind == 1:  # massing model photo: grey board, white blocks with side shading
        im.paste((176, 172, 166), [0, 0, w, h]); d = ImageDraw.Draw(im); d.rectangle([int(w * .05), int(h * .6), int(w * .95), int(h * .95)], fill=(222, 220, 214))
        for _ in range(9):
            bw, bh = r.randint(w // 12, w // 5), r.randint(h // 8, h // 3); x, y = r.randint(int(w * .08), int(w * .8)), r.randint(int(h * .45), int(h * .75)); dx = bw // 4
            d.polygon([(x, y), (x + bw, y), (x + bw + dx, y - dx), (x + dx, y - dx)], fill=(250, 250, 248)); d.rectangle([x, y, x + bw, y + bh], fill=(236, 234, 228)); d.polygon([(x + bw, y), (x + bw + dx, y - dx), (x + bw + dx, y + bh - dx), (x + bw, y + bh)], fill=(196, 194, 188))
    else:  # section linework on white; tight=True fills the frame (no internal white bands)
        im.paste((250, 250, 248), [0, 0, w, h]); d = ImageDraw.Draw(im); top, gy = (int(h * .06), int(h * .92)) if tight else (int(h * .25), int(h * .7))
        d.line([(0, gy), (w, gy)], fill=(20, 20, 20), width=5)
        for k in range(4):
            x0 = int(w * (.04 + .24 * k)) if tight else int(w * (.1 + .2 * k)); bw = int(w * .21) if tight else int(w * .17)
            d.rectangle([x0, top, x0 + bw, gy], outline=(20, 20, 20), width=3)
            for f in range(1, 4): d.line([(x0, gy - f * (gy - top) // 4), (x0 + bw, gy - f * (gy - top) // 4)], fill=(60, 60, 60), width=1)
        d.line([(int(w * .02), top - int(h * .03)), (int(w * .98), top - int(h * .03))], fill=(20, 20, 20), width=2)
    d.text((16, 12), f"SYNTHETIC {label}", fill=(40, 40, 40)); im.save(path)

def plan(path, w=841, h=594, tight=False):
    m = 6 if tight else 40
    c = canvas.Canvas(str(path), pagesize=(w, h)); c.setLineWidth(0.4)
    for i in range(0, 60):
        c.line(m + i * 12, m, m + i * 12, h - m) if i % 2 == 0 else c.line(m, m + i * 8, w - m, m + i * 8)
    c.rect(m + 80, m + 80, w - 2 * m - 160, h - 2 * m - 160); c.circle(w / 2, h / 2, 90); c.drawString(m + 4, m + 4, "SYNTHETIC PLAN - vector linework"); c.save()

def project(name, title, imgs, text_len, with_plan=True, tight=False, sections=None):
    d = OUT / name; (d / "images").mkdir(parents=True, exist_ok=True); (d / "drawings").mkdir(exist_ok=True)
    for i, (w, h) in enumerate(imgs): img(d / "images" / f"img{i+1:02d}.png", w, h, hash((name, i)) & 0xffff, f"{name}-{i+1}", tight)
    if with_plan: plan(d / "drawings" / "plan01.pdf", tight=tight)
    if sections:
        NL = chr(10)
        (d / "project.md").write_text("# " + title + NL + "domain: architecture" + NL + "audience: graduate admissions" + NL + "keywords: harbour, timber, public bath, threshold" + NL + "".join(NL + "## " + k + NL + v + NL for k, v in sections.items()), encoding="utf-8")
        return
    body = " ".join(["The scheme organizes public program around a shifted courtyard and a long timber roof."] * text_len)
    (d / "project.md").write_text(f"# {title}\ndomain: architecture\naudience: graduate admissions\nkeywords: housing, courtyard, timber, urban infill\n\n## Concept\n{body}\n\n## Site\nSynthetic site description for tests only.\n\n## Role\nIndividual work, 14 weeks.\n", encoding="utf-8")


def domain_img(path, w, h, seed, kind, label):
    """SYNTHETIC non-architecture images: ui screen, brand mark/swatch, photo-like gradient scene."""
    r = random.Random(seed); im = Image.new("RGB", (w, h), (245, 245, 247)); d = ImageDraw.Draw(im)
    if kind == "ui":  # phone screen: status bar, header card, list rows, bottom tab bar
        d.rectangle([0, 0, w, int(h * .05)], fill=(30, 30, 34)); d.rectangle([int(w * .06), int(h * .09), int(w * .94), int(h * .30)], fill=(70 + r.randint(0, 80), 110, 220))
        for i in range(5): y = int(h * (.34 + i * .09)); d.rectangle([int(w * .06), y, int(w * .94), y + int(h * .07)], fill=(255, 255, 255), outline=(220, 220, 224)); d.ellipse([int(w * .09), y + 8, int(w * .09) + 40, y + 48], fill=(180 + r.randint(0, 60), 190, 200))
        d.rectangle([0, int(h * .93), w, h], fill=(255, 255, 255))
    elif kind == "brand":  # mark on a flat colour field with swatches
        base = (r.randint(20, 235), r.randint(20, 235), r.randint(20, 235)); im.paste(base, [0, 0, w, h]); d = ImageDraw.Draw(im)
        d.ellipse([w * .3, h * .25, w * .7, h * .75], outline=(255, 255, 255), width=max(6, w // 60)); d.rectangle([w * .42, h * .42, w * .58, h * .58], fill=(255, 255, 255))
        for i in range(4): d.rectangle([w * (.1 + .2 * i), h * .86, w * (.2 + .2 * i), h * .94], fill=(r.randint(0, 255), r.randint(0, 255), r.randint(0, 255)))
    else:  # photo-like: sky/ground gradient with a soft subject
        for y in range(h): c = int(40 + 190 * y / h); d.line([(0, y), (w, y)], fill=(c, int(c * .8) + 20, 150 - c // 3 + 60))
        d.ellipse([w * .35, h * .3, w * .65, h * .7], fill=(30 + r.randint(0, 60), 30, 40))
    d.text((12, 8), f"SYNTHETIC {label}", fill=(120, 120, 120)); im.save(path)


def domain_project(name, title, domain, keywords, kinds_sizes, sections, audience="art-school admissions"):
    d = OUT / name; (d / "images").mkdir(parents=True, exist_ok=True)
    for i, (kind, (w, h)) in enumerate(kinds_sizes): domain_img(d / "images" / f"img{i+1:02d}.png", w, h, hash((name, i)) & 0xffff, kind, f"{name}-{i+1}")
    NL = chr(10)
    body = "".join(NL + "## " + k + NL + v + NL for k, v in sections.items())
    (d / "project.md").write_text("# " + title + NL + "domain: " + domain + NL + "audience: " + audience + NL + "keywords: " + ", ".join(keywords) + NL + body, encoding="utf-8")


if __name__ == "__main__":
    project("arch_01", "Courtyard Housing", [(1600, 1000), (1000, 1500), (1200, 1200), (2000, 800)], 3)
    project("arch_02", "Timber Library", [(1500, 1000)] * 3 + [(800, 1400)], 12)          # long text -> overflow stress
    project("arch_03", "Micro Pavilion", [(1600, 900), (900, 1600)], 1, with_plan=False)   # few assets
    project("arch_04", "Harbour Baths", [(1800, 1200), (1200, 1600), (1600, 1000), (2000, 900), (1400, 1400)], 4, tight=True, sections={
        "Concept": "A public bath sits on the edge of the old harbour, where a timber deck folds into a sequence of pools and a long roof shelters the walk between them. The building is a threshold between the town and the water: the pools step down with the tide, and the changing rooms are tucked under the deck so the horizon stays open.",
        "Site": "The site is a disused quay with a stone edge and a working slipway. The deck keeps the quay line and lifts only where the baths need depth.",
        "Structure": "Glulam portal frames at three-metre centres carry the roof; the deck is a sacrificial larch skin over a steel grillage.",
        "Role": "Individual work, 12 weeks, third year."})
    domain_project("ux_01", "Transit Companion App", "ux-product", ["mobile", "transit", "onboarding", "accessibility"],
                   [("ui", (750, 1500))] * 4 + [("ui", (1500, 1000))], {"Problem": "Synthetic problem statement for tests only.", "Process": "Synthetic research and iteration summary. " * 4, "Outcome": "Synthetic outcome metrics are placeholders."})
    domain_project("brand_01", "Studio Mark Identity", "graphic-branding", ["identity", "logo", "colour", "packaging"],
                   [("brand", (1600, 1600)), ("brand", (1600, 900)), ("brand", (900, 1600)), ("brand", (2000, 800))], {"Brief": "Synthetic brief for tests only.", "System": "Synthetic identity system description. " * 3})
    domain_project("photo_01", "Winter Harbour Series", "photography", ["series", "documentary", "light", "harbour"],
                   [("photo", (1800, 1200)), ("photo", (1200, 1800)), ("photo", (1500, 1500)), ("photo", (2400, 800)), ("photo", (1200, 1800)), ("photo", (1800, 1200))], {"Statement": "Synthetic artist statement for tests only."})
    print("fixtures ok", OUT)
