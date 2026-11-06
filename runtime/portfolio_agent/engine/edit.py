"""Local edits with preservation proof.

edit_element(): change ONE element (text and/or scale), optionally run bounded auto-repair, then verify:
 (a) scene diff only touches the target (+ ids the repair touched, reported as `reflowed`),
 (b) page QA passes, (c) rendered pixels outside target+reflowed boxes are unchanged, (d) every other page renders byte-identical.
Nothing is written unless all checks pass.
"""
import json
import copy
from pathlib import Path
import fitz
import numpy as np
from portfolio_agent.core.guardrails import gates, repair
from portfolio_agent.core.geometry import PT_PER_MM
from . import registry


def _pix(pdf, i, dpi=72):
    d = fitz.open(pdf)
    p = d[i].get_pixmap(dpi=dpi)
    d.close()
    return p


def edit_element(out_dir, page_id, element_id, text=None, scale=None, auto_repair=False):
    out = Path(out_dir)
    run = json.loads((out / "run.json").read_text(encoding="utf-8"))
    spec = run["spec"]
    be = registry.get_backend(run.get("backend", "local"))
    be.configure(spec.get("style"))
    root = run["project_dir"]
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    A = {a["id"]: a for a in manifest["assets"]}
    files = sorted((out / "scenes").glob("page-*.json"))
    scenes = [json.loads(f.read_text(encoding="utf-8")) for f in files]
    idx = next(i for i, s in enumerate(scenes) if s["page_id"] == page_id)
    before = copy.deepcopy(scenes[idx])
    old_pdf, new_pdf = out / "book.pdf", out / "book.edited.pdf"
    tgt = next(e for e in scenes[idx]["elements"] if e["id"] == element_id)
    if text is not None and tgt.get("locked"):
        return {"ok": False, "reason": "LOCKED_TARGET"}
    if text is not None:
        tgt["text"] = text
    reflowed = []
    relayout = scale is not None and tgt["kind"] in ("image", "pdf-region")
    if relayout:  # graphic resize = ask the author to re-solve THIS page with a larger weight; neighbours may move (declared), content never changes
        author = registry.get_author(run.get("author", "rule_based"))
        if not author.can_relayout:
            return {"ok": False, "reason": "RELAYOUT_UNSUPPORTED_BY_AUTHOR", "author": author.name}
        plan = json.loads((out / "plan.json").read_text(encoding="utf-8"))
        new = author.relayout(plan["pages"][idx], before, manifest, spec, {tgt["asset_id"]: scale ** 2})
        old_by = {e["id"]: e for e in before["elements"]}
        if {e["id"] for e in new["elements"]} != set(old_by):
            return {"ok": False, "reason": "ELEMENT_SET_CHANGED"}
        for e in new["elements"]:
            if e.get("text") != old_by[e["id"]].get("text") or e.get("asset_id") != old_by[e["id"]].get("asset_id"):
                return {"ok": False, "reason": "CONTENT_CHANGED_BY_RELAYOUT"}
        scenes[idx] = new
        reflowed = [e["id"] for e in new["elements"] if e["id"] != element_id and e["box_mm"] != old_by[e["id"]]["box_mm"]]
    elif scale is not None:  # non-graphic: scale box, keep top-left
        x, y, w, h = tgt["box_mm"]
        tgt["box_mm"] = [x, y, round(w * scale, 2), round(h * scale, 2)]
    if auto_repair:
        r = repair.repair_scene(scenes[idx], manifest, spec, be)
        reflowed = sorted(set(reflowed) | {i for i in r["touched"] if i != element_id})
    diff = gates.CED.diff_scene(before, scenes[idx], [element_id], reflowed)
    if relayout:  # a graphic's lock protects its CONTENT; moving/resizing it on re-layout is allowed
        diff = [d for d in diff if d["code"] != "LOCKED_TARGET_EDITED"]
    grew = None
    if relayout:
        nb = next(e for e in scenes[idx]["elements"] if e["id"] == element_id)["box_mm"]
        ob = tgt["box_mm"]
        grew = round((nb[2] * nb[3]) / (ob[2] * ob[3]), 3)
        if grew < 1.1:
            diff.append({"code": "TARGET_NOT_ENLARGED", "element": element_id, "area_ratio": grew})
    page_issues = gates.qa_scene(scenes[idx], manifest, spec, be)
    be.export(scenes, manifest, root, out / "book.edited", spec, ["pdf"])
    b = spec.get("bleed_mm", 0)
    m = PT_PER_MM
    boxes = [e["box_mm"] for e in scenes[idx]["elements"] if e["id"] in [element_id] + reflowed] + [e["box_mm"] for e in before["elements"] if e["id"] in [element_id] + reflowed]
    changed_outside, other_pages_changed = 0, []
    for i in range(len(scenes)):
        a, c = _pix(old_pdf, i), _pix(new_pdf, i)
        if i != idx:
            if a.samples != c.samples:
                other_pages_changed.append(i + 1)
            continue
        A_ = np.frombuffer(a.samples, np.uint8).reshape(a.height, a.width, a.n)
        C_ = np.frombuffer(c.samples, np.uint8).reshape(a.height, a.width, a.n)
        mask = np.ones((a.height, a.width), bool)
        for x, y, w, h in boxes:
            mask[max(0, int((y + b - 1) * m)):int((y + h + b + 1) * m) + 2, max(0, int((x + b - 1) * m)):int((x + w + b + 1) * m) + 2] = False
        changed_outside = int(((A_ != C_).any(axis=2) & mask).sum())
    ok = not diff and not page_issues and changed_outside == 0 and not other_pages_changed
    if ok:
        files[idx].write_text(json.dumps(scenes[idx], indent=1), encoding="utf-8")
        new_pdf.replace(old_pdf)
    elif new_pdf.exists():
        new_pdf.unlink()
    return {"ok": ok, "area_ratio": grew, "scene_diff": diff, "qa_issues": page_issues, "reflowed": reflowed, "pixels_changed_outside_target": changed_outside, "other_pages_changed": other_pages_changed}


def edit_text(out_dir, page_id, element_id, new_text):
    return edit_element(out_dir, page_id, element_id, text=new_text)
