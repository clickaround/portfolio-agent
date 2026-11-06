"""Bounded targeted repair: touches only elements named by an issue, max N rounds, verified by diff_scene. Never edits locked content
semantically (text is never rewritten/truncated; only font size/box geometry change)."""
import copy
from ..geometry import fit
from ..conventions import is_title
from .gates import qa_scene, CED


def _els(sc):
    return {e["id"]: e for e in sc["elements"]}


def repair_scene(sc, manifest, spec, measurer, max_rounds=3):
    A = {a["id"]: a for a in manifest["assets"]}
    s = min(spec["width_mm"], spec["height_mm"]) / 210.0
    m = spec["margin_mm"]
    W, H = sc["size_mm"]
    before = copy.deepcopy(sc)
    log = []
    touched = set()
    for rnd in range(max_rounds):
        issues = qa_scene(sc, manifest, spec, measurer)
        todo = [i for i in issues if i["code"] in ("TEXT_OVERFLOW", "OUTSIDE_MARGIN", "ASPECT_DISTORTION")]
        if not todo:
            break
        E = _els(sc)
        for i in todo:
            e = E[i["elements"][0]]
            x, y, w, h = e["box_mm"]
            if i["code"] == "TEXT_OVERFLOW":
                fs = e.get("font_size_pt", 10)
                while fs > 7 * s and not measurer.text_fits(e["text"], w, h, fs, is_title(e["id"]), e.get("style")):
                    fs = round(fs - 0.5, 1)
                if measurer.text_fits(e["text"], w, h, fs, is_title(e["id"]), e.get("style")):
                    e["font_size_pt"] = fs
                    log.append({"round": rnd, "element": e["id"], "fix": f"font -> {fs}pt"})
                    touched.add(e["id"])
            elif i["code"] == "OUTSIDE_MARGIN":
                nw, nh = min(w, W - 2 * m), min(h, H - 2 * m)
                if e["kind"] in ("image", "pdf-region"):
                    ar = A[e["asset_id"]]["aspect"]
                    nx, ny, nw, nh = fit(ar, [m, m, nw, nh])
                else:
                    nx, ny = min(max(x, m), W - m - nw), min(max(y, m), H - m - nh)
                e["box_mm"] = [round(nx, 2), round(ny, 2), round(nw, 2), round(nh, 2)]
                if e["kind"] in ("image", "pdf-region"):
                    e["box_mm"] = [round(min(max(e["box_mm"][0], m), W - m - e["box_mm"][2]), 2), round(min(max(e["box_mm"][1], m), H - m - e["box_mm"][3]), 2), e["box_mm"][2], e["box_mm"][3]]
                log.append({"round": rnd, "element": e["id"], "fix": "clamped into margin"})
                touched.add(e["id"])
            elif i["code"] == "ASPECT_DISTORTION":
                e["box_mm"] = fit(A[e["asset_id"]]["aspect"], e["box_mm"])
                log.append({"round": rnd, "element": e["id"], "fix": "re-fit to source aspect"})
                touched.add(e["id"])
    off = [d for d in CED.diff_scene(before, sc, sorted(touched)) if d["code"] == "UNEXPECTED_EDIT"]
    return {"touched": sorted(touched), "log": log, "unexpected_edits": off, "remaining": qa_scene(sc, manifest, spec, measurer)}
