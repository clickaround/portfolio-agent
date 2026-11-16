"""Set C (design section 5): a teacher model writes the layout of a page in the page DSL; the reward keeps or drops it.

  gen_c.py RUN_DIR OUT_DIR [--model sonnet] [--pages page-02 ...] [--keep 0.8]

For every page of the run: the problem (page_dsl.problem) plus the first words of each text go to `claude -p`; the answer is parsed,
decoded and scored (reward.score). Written per page: <page>.json with problem, answer, score, kept, and <page>.png, a wireframe of
the engine's layout beside the teacher's (boxes only; this is for a first look, not a rendered page).
A sample is kept when no blocking gate fires and total >= --keep. The judge step (a second model looking at the rendered page) is
NOT here yet, so nothing this writes is training data until that exists.
The engine's own layout is never shown to the teacher: the point is a layout that does not come from our rules.
"""
import argparse
import json
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw
import page_dsl as D
import reward as R

PROMPT = """You lay out one page of a design portfolio. Units are millimetres. The page line gives width, height and the margin (m).
Each element line is: id, kind, then for image/drawing the aspect ratio (width / height), for text the type size in pt and the number of characters.
Lines starting with "fixed" (x y w h) are things already on the page, such as the running header: keep clear of them.
Answer with one line per element: id x y w   (whole numbers; x, y = top-left corner, w = width). Then a line with the word end.
You do not give heights: a picture's height is w / aspect, a text block's height follows from its width and type size.
Rules: everything inside the margins; nothing overlaps; a caption sits directly under its picture, same left edge; pictures are the
largest things on the page; align left edges to a few shared columns; do not leave a wide empty band across the page.
Answer with the lines only, no other text.

{problem}
Texts (first words): {texts}
"""
COL = {"image": (70, 110, 160), "drawing": (90, 140, 110), "title": (40, 40, 40), "body": (120, 120, 120), "caption": (190, 110, 60), "label": (180, 60, 60), "text": (120, 120, 120)}


def wire(sc, spec, px=3):
    W, H = sc["size_mm"]
    im = Image.new("RGB", (round(W * px), round(H * px)), "white")
    d = ImageDraw.Draw(im)
    m = spec["margin_mm"]
    d.rectangle([m * px, m * px, (W - m) * px, (H - m) * px], outline=(225, 225, 225))
    for e in D.content(sc):
        x, y, w, h = e["box_mm"]
        k = D.kind_of(e)
        d.rectangle([x * px, y * px, (x + w) * px, (y + h) * px], outline=COL[k], width=2, fill=(232, 238, 245) if e["kind"] != "text" else None)
        d.text((x * px + 3, y * px + 1), k, fill=COL[k])
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("out")
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--pages", nargs="*")
    ap.add_argument("--keep", type=float, default=0.8)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    spec, manifest, scenes, measurer = D.load_run(a.run)
    kept = 0
    for sc in scenes:
        if a.pages and sc["page_id"] not in a.pages:
            continue
        prob = D.problem(sc, manifest, spec, 1)
        texts = "; ".join(f"{n}: {e['text'][:40]!r}" for n, e in enumerate(D.content(sc)) if e["kind"] == "text")
        r = subprocess.run(["claude", "-p", "--model", a.model], input=PROMPT.format(problem=prob, texts=texts), capture_output=True, text=True, encoding="utf-8", shell=True)
        ans = "\n".join(ln for ln in r.stdout.strip().splitlines() if ln.strip() and not ln.startswith("```")) + "\n"
        s = R.score(ans, sc, manifest, spec, measurer, 1)
        keep = s["passed"] and s["total"] >= a.keep
        kept += keep
        base = R.score(D.encode(sc, 1), sc, manifest, spec, measurer, 1)
        (out / f"{sc['page_id']}.json").write_text(json.dumps({"problem": prob, "answer": ans, "score": s, "kept": keep, "engine_score": base["total"], "model": a.model, "source": "claude"}, indent=1, ensure_ascii=False), encoding="utf-8")
        new = D.decode(ans, sc, manifest, measurer, 1)
        left, right = wire(sc, spec), wire(new, spec) if new else Image.new("RGB", wire(sc, spec).size, (250, 230, 230))
        sheet = Image.new("RGB", (left.width * 2 + 20, left.height + 16), "white")
        sheet.paste(left, (0, 16))
        sheet.paste(right, (left.width + 20, 16))
        ImageDraw.Draw(sheet).text((4, 2), f"{sc['page_id']}   left: engine {base['total']}   right: {a.model} {s['total']} {'KEPT' if keep else 'dropped ' + ','.join(s['blocking'])}", fill=(0, 0, 0))
        sheet.save(out / f"{sc['page_id']}.png")
        print(sc["page_id"], "teacher", s["total"], s["terms"], s["blocking"] or "pass", "KEPT" if keep else "dropped", "| engine", base["total"])
    print("kept", kept)


if __name__ == "__main__":
    main()
