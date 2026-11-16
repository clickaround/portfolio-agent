"""T1016: the gates as one number a model can be trained against (design section 7, stage 2; shape after FLOORA arXiv 2609.36064
appendix E, DOC_REPORTED: every term in [0, 1], a smooth step past the tolerance, hard terms combined by geometric mean so that one
failure pulls the whole score down, output that does not parse scores 0).

  hard   margin   every placed element inside the margins        error = worst overshoot, mm        tolerance 1 mm
         overlap  no two placed elements on top of each other    error = overlapped share of the content area   tolerance 0.5 %
         (aspect ratio and text fit cannot fail: the format has no height, see page_dsl.py)
  soft   caption  each caption directly under or over a picture  error = gap to the nearest picture edge, mm    tolerance 6 mm
         band     no tall empty band across the page             error = tallest empty band / content height    tolerance 25 %
         align    left edges shared with another element or the margin   share of elements
  total = hard * (1 + soft) / 2      0 for an unusable layout, 1 for a clean one; `passed` is the product's own verdict (no blocking gate)

The soft terms are HYPOTHESIS: they encode what was seen on our pages (detached captions, the empty band of 2026-11-14), nothing else.
They do not say a page is good, only that it is not broken in a known way.

  reward.py RUN_DIR [--u 1]     per page: the page as laid out, the same content dropped in one column, and a garbage answer
"""
import argparse
import math
import page_dsl as D

TAU = {"margin": 1.0, "overlap": 0.005, "caption": 6.0, "band": 0.25}


def step(e, tau):
    return 1.0 if e <= tau else math.exp(-(e - tau) / tau)


def _ov(a, b):
    return max(0.0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])) * max(0.0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))


def score(layout_text, sc, manifest, spec, measurer, u=3):
    from portfolio_agent.core.guardrails import gates
    new = D.decode(layout_text, sc, manifest, measurer, u)
    if new is None:
        return {"total": 0.0, "hard": 0.0, "soft": 0.0, "passed": False, "terms": {"parse": 0.0}, "blocking": ["UNPARSEABLE"]}
    W, H = new["size_mm"]
    m = spec["margin_mm"]
    els = D.content(new)
    box = [e["box_mm"] for e in els]
    over = max([0.0] + [max(m - x, m - y, x + w - (W - m), y + h - (H - m)) for x, y, w, h in box])
    area = (W - 2 * m) * (H - 2 * m)
    lap = sum(_ov(box[i], box[j]) for i in range(len(box)) for j in range(i) if not (els[i].get("allow_overlap") or els[j].get("allow_overlap")))
    lap += sum(_ov(b, f) for b in box for f in D.fixed(new))
    t = {"parse": 1.0, "margin": step(over, TAU["margin"]), "overlap": step(lap / area, TAU["overlap"])}
    hard = math.exp((math.log(max(t["margin"], 1e-8)) + math.log(max(t["overlap"], 1e-8))) / 2)

    pics = [b for e, b in zip(els, box) if e["kind"] != "text"]
    caps = [b for e, b in zip(els, box) if D.kind_of(e) == "caption"]
    if caps and pics:
        def gap(c):
            near = [min(abs(c[1] - (p[1] + p[3])), abs(p[1] - (c[1] + c[3]))) for p in pics if min(c[0] + c[2], p[0] + p[2]) - max(c[0], p[0]) > 0]
            return min(near) if near else 1e9
        t["caption"] = sum(step(gap(c), TAU["caption"]) for c in caps) / len(caps)
    spans, y, band = sorted((max(b[1], m), min(b[1] + b[3], H - m)) for b in box), m, 0.0
    for a, b in spans + [(H - m, H - m)]:
        band, y = max(band, a - y), max(y, b)
    t["band"] = step(band / (H - 2 * m), TAU["band"])
    lefts = [round(b[0], 1) for b in box]
    t["align"] = sum(1 for x in lefts if abs(x - m) < 0.6 or lefts.count(x) > 1) / len(lefts) if lefts else 1.0
    soft = sum(t[k] for k in ("caption", "band", "align") if k in t) / sum(1 for k in ("caption", "band", "align") if k in t)
    blocking = sorted({i["code"] for i in gates.split(gates.qa_scene(new, manifest, spec, measurer))[0]})
    return {"total": round(hard * (1 + soft) / 2, 4), "hard": round(hard, 4), "soft": round(soft, 4), "passed": not blocking,
            "terms": {k: round(v, 3) for k, v in t.items()}, "blocking": blocking}


def one_column(sc, spec, u):
    """A deliberately poor answer: everything at the left margin, one grid step wide per 10 % of the page, stacked from the top."""
    c, m = round(sc["size_mm"][0] / u), round(spec["margin_mm"] / u)
    return "".join(f"{n} {m} {m + 2 * n} {max(1, (c - 2 * m) // 3)}\n" for n in range(len(D.content(sc)))) + "end\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--u", type=int, default=1)
    a = ap.parse_args()
    spec, manifest, scenes, measurer = D.load_run(a.run)
    for sc in scenes:
        r = score(D.encode(sc, a.u), sc, manifest, spec, measurer, a.u)
        bad = score(one_column(sc, spec, a.u), sc, manifest, spec, measurer, a.u)
        junk = score("0 1 1\nend\n", sc, manifest, spec, measurer, a.u)
        print(sc["page_id"], "as laid out", r["total"], r["terms"], r["blocking"] or "pass", "| stacked", bad["total"], bad["blocking"], "| junk", junk["total"])


if __name__ == "__main__":
    main()
