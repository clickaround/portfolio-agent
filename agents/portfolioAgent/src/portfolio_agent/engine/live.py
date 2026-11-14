"""Conversation-time editing of the DesignCraft document: one small edit at a time, checked, kept or thrown away.

The user (or the host LLM on the user's behalf) points at something and says what to change. The host turns that into typed ops
(backends/designcraft/live.py TOOLS) and calls edit(). Nothing is regenerated: only the named elements change.

  context(out, page_id, x, y)   what the LLM needs for ONE page: the marked element, its neighbours, the tools, the open issues
  edit(out, ops, marked)        apply -> check scope -> check gates -> keep (next step) or reject with reasons the LLM can act on
  sync(out, file)               the user saved the document from the editor: take their changes in and protect them
  undo(out)                     one step back

Rules (papers read 2026-11-14, DOC_REPORTED; ACE arXiv 2608.24103, APEX arXiv 2601.04794, Cleo arXiv 2603.02050):
 - an edit may change only the elements its ops name (OFF_TARGET otherwise);
 - an edit that adds a blocking gate issue is not kept, and the issue text goes back as the critique;
 - what the user changed by hand is theirs: an agent op on such an element is refused unless the user marked that element.

State lives in <out>/live/: NNN.designcraft, NNN.pdf, NNN.scenes.json and state.json. scenes/ always mirrors the current step.
"""
import copy
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path
from portfolio_agent.core.guardrails import gates
from . import registry


def _load(out):
    out = Path(out)
    run = json.loads((out / "run.json").read_text(encoding="utf-8"))
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    files = sorted((out / "scenes").glob("page-*.json"))
    scenes = [json.loads(f.read_text(encoding="utf-8")) for f in files]
    measurer = registry.get_backend(run.get("backend", "local"))
    measurer.configure(run["spec"].get("style"))
    return out, run, manifest, files, scenes, measurer


def _dc():
    """The DesignCraft live-edit module, loaded by path like every backend (registry is the only place that knows where backends are)."""
    path = registry.backend_dir("designcraft") / "live.py"
    spec = importlib.util.spec_from_file_location("pa_backend_designcraft_live", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _state(out):
    f = Path(out) / "live" / "state.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else None


def _save_state(out, st):
    (Path(out) / "live" / "state.json").write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")


def _file(out, step, ext):
    return Path(out) / "live" / f"{step:03d}.{ext}"


def _key(sc, e):
    return f"{sc['page_id']}/{e['id']}"


def _blocking(scenes, manifest, spec, measurer):
    """Blocking issues of every page as comparable keys -> {(page, code, elements): details}."""
    out = {}
    for sc in scenes:
        for i in gates.split(gates.qa_scene(sc, manifest, spec, measurer))[0]:
            out[(sc["page_id"], i["code"], tuple(sorted(i.get("elements", []))))] = i.get("details", "")
    return out


def _on_pages(scenes):
    return {e["asset_id"] for sc in scenes for e in sc["elements"] if e.get("asset_id") and e.get("visible") is not False}


def _merge(scenes, doc, by, touched):
    """Scenes with the document's geometry, text and visibility written in. `touched` keys get edited_by=`by`."""
    live = {it["key"]: it for pg in doc["pages"] for it in pg["items"]}
    out = copy.deepcopy(scenes)
    for sc in out:
        keep = []
        for e in sc["elements"]:
            k = _key(sc, e)
            exported = e.get("visible") is not False and (e["kind"] != "text" or e.get("text"))   # the exporter makes no object for the rest
            if k not in live:
                if not exported:
                    keep.append(e)
                continue                                 # removed in the document
            it = live[k]
            e["box_mm"] = it["box_mm"]
            if "text" in it:
                e["text"] = it["text"]
            if it["hidden"]:
                e["visible"] = False
            if k in touched:
                e["edited_by"] = by
            keep.append(e)
        sc["elements"] = keep
    return out


def start(out_dir):
    """Export the current scenes as step 0 of a live session (a fresh session replaces the pointer; old files stay)."""
    out, run, manifest, files, scenes, measurer = _load(out_dir)
    (out / "live").mkdir(exist_ok=True)
    be = registry.get_backend("designcraft")
    r = be.export(scenes, manifest, run["project_dir"], out / "live" / "000", run["spec"], ["pdf", "native"])
    if r["exit"] != 0 or not r["files"].get("native"):
        return {"ok": False, "reason": "EXPORT_FAILED", "notes": r["notes"]}
    _file(out, 0, "scenes.json").write_text(json.dumps(scenes, ensure_ascii=False), encoding="utf-8")
    _save_state(out, {"step": 0, "history": []})
    return {"ok": True, "step": 0, "document": str(_file(out, 0, "designcraft")), "notes": r["notes"]}


def context(out_dir, page_id, x_mm=None, y_mm=None):
    """Everything the LLM needs to edit ONE page, and nothing about the other pages (object data, not a screenshot)."""
    out, run, manifest, files, scenes, measurer = _load(out_dir)
    dc, st = _dc(), _state(out)
    if st is None:
        return {"ok": False, "reason": "NO_LIVE_SESSION"}
    doc = dc.read(_file(out, st["step"], "designcraft"))
    pi = next(i for i, s in enumerate(scenes) if s["page_id"] == page_id)
    sc = scenes[pi]
    A = {a["id"]: a for a in manifest["assets"]}
    by_key = {_key(sc, e): e for e in sc["elements"]}
    els = []
    for it in doc["pages"][pi]["items"]:
        e = by_key.get(it["key"], {})
        row = {"key": it["key"], "kind": it["kind"], "box_mm": it["box_mm"]}
        if "text" in it:
            row["text"] = it["text"] if len(it["text"]) <= 160 else it["text"][:160] + "…"
            row["font_size_pt"] = e.get("font_size_pt")
        if e.get("asset_id"):
            a = A[e["asset_id"]]
            row["asset"] = {"id": a["id"], "aspect": a["aspect"], "role": a.get("role"), "crop_allowed": bool(a.get("crop_allowed"))}
        if e.get("edited_by") == "user":
            row["edited_by"] = "user"
        if it["locked"]:
            row["locked"] = True
        els.append(row)
    marked = []
    if x_mm is not None and y_mm is not None:
        marked = dc.hit(doc, pi, x_mm, y_mm) or dc.nearest(doc, pi, x_mm, y_mm, 2)
    issues = [{"code": c, "elements": list(e), "details": d} for (p, c, e), d in _blocking([sc], manifest, run["spec"], measurer).items()]
    return {"ok": True, "step": st["step"], "page_id": page_id, "size_mm": sc["size_mm"], "margin_mm": run["spec"]["margin_mm"],
            "mark_mm": [x_mm, y_mm] if marked else None, "marked": marked, "elements": els, "blocking_issues": issues,
            "tools": {**dc.TOOLS, "replace_image": "{target, asset_id} put another source into a picture frame; the frame takes the new picture's shape"},
            "assets_available": [{"id": a["id"], "aspect": a["aspect"], "role": a.get("role")} for a in manifest["assets"]],
            "rules": ["only the elements your ops name may change", "an op on an element with edited_by=user is refused unless that element is marked",
                      "a picture keeps its aspect ratio: give set_box any box and the picture is fitted inside it",
                      "replace_image takes asset_id from assets_available, never a path"]}


def _contain(box, aspect):
    """The largest box of `aspect` inside `box`, centred."""
    x, y, w, h = box
    nw, nh = (w, w / aspect) if w / aspect <= h else (h * aspect, h)
    return [round(x + (w - nw) / 2, 2), round(y + (h - nh) / 2, 2), round(nw, 2), round(nh, 2)]


def _prepare(ops, scenes, manifest, project_dir, marked, by):
    """Ops as the document layer runs them, plus the ones refused before anything runs."""
    A = {a["id"]: a for a in manifest["assets"]}
    el = {_key(sc, e): e for sc in scenes for e in sc["elements"]}
    flat, refused, swaps = [], [], {}
    for op in ops:
        op = dict(op)
        e = el.get(op.get("target"))
        if e is not None and by == "agent" and e.get("edited_by") == "user" and op["target"] not in marked:
            refused.append({"op": op.get("op"), "target": op["target"], "ok": False, "error": "USER_EDITED: the user set this by hand; ask, or have them mark it"})
            continue
        if e is not None and e.get("asset_id"):
            aspect = A[e["asset_id"]]["aspect"]
            if op.get("op") == "replace_image":
                a = A.get(op.get("asset_id"))
                if a is None:
                    refused.append({"op": "replace_image", "target": op["target"], "ok": False, "error": f"unknown asset_id; known: {sorted(A)}"})
                    continue
                swaps[op["target"]] = a["id"]   # put the file in, then give the frame the new picture's shape
                flat.append({**op, "path": str(Path(project_dir) / a["relative_path"])})
                flat.append({"op": "set_box", "target": op["target"], "box_mm": _contain(e["box_mm"], a["aspect"])})
                continue
            box = op.get("box_mm")
            if op.get("op") == "set_box" and not e.get("crop") and isinstance(box, (list, tuple)) and len(box) == 4 and min(box[2:]) > 0:
                op["box_mm"] = _contain(box, aspect)
        flat.append(op)
    return flat, refused, swaps


def edit(out_dir, ops, marked=(), by="agent"):
    out, run, manifest, files, scenes, measurer = _load(out_dir)
    dc, st = _dc(), _state(out)
    if st is None:
        return {"ok": False, "reason": "NO_LIVE_SESSION"}
    spec = run["spec"]
    flat, refused, swaps = _prepare(ops, scenes, manifest, run["project_dir"], set(marked), by)
    before_issues = _blocking(scenes, manifest, spec, measurer)
    step = st["step"] + 1
    with tempfile.TemporaryDirectory() as t:
        r = dc.apply(_file(out, st["step"], "designcraft"), flat, Path(t) / "next.designcraft", Path(t) / "next.pdf")
        results = refused + r["results"]
        targets = {x["target"] for x in r["results"] if x["ok"]}
        diff = dc.changed(r["before"], r["after"])
        entry = {"step": step, "by": by, "ops": list(ops), "results": results, "changed": diff}
        reason, critique = None, []
        if not targets:
            reason, critique = "NOTHING_APPLIED", [f"{x['op']} {x['target']}: {x.get('error')}" for x in results]
        elif set(diff) - targets:
            reason, critique = "OFF_TARGET", [f"{k} changed ({', '.join(v)}) but no op named it" for k, v in diff.items() if k not in targets]
        new_scenes = _merge(scenes, r["after"], by, targets)
        sizes = {op["target"]: op["size"] for op, x in zip(flat, r["results"]) if x["ok"] and op.get("op") == "text_style" and "size" in op}
        for sc in new_scenes:
            for e in sc["elements"]:
                k = _key(sc, e)
                if k in swaps and k in targets:
                    e["asset_id"] = swaps[k]
                if k in sizes:   # the document read-back carries no type size: the scene must, or the text-fit gate measures the old size
                    e["font_size_pt"] = sizes[k]
                    diff[k] = sorted(set(diff.get(k, [])) | {"style"})
        was, now = dc.index(r["before"]), dc.index(r["after"])
        overset = sorted(k for k, (_, it) in now.items() if it.get("overset") and not (k in was and was[k][1].get("overset")))
        if reason is None:
            after_issues = _blocking(new_scenes, manifest, spec, measurer)
            new = [k for k in after_issues if k not in before_issues]
            gone = sorted(_on_pages(scenes) - _on_pages(new_scenes)) if by == "agent" else []
            if new or gone or overset:
                reason = "GATE"
                critique = ([f"{p} {c} {list(e)}: {after_issues[(p, c, e)]}" for p, c, e in new] + [f"source {a} would no longer be on any page" for a in gone]
                            + [f"{k}: the text no longer fits its frame in the document" for k in overset])
            entry["fixed_issues"] = [list(k) for k in before_issues if k not in after_issues]
        if reason:
            st["history"].append({**entry, "accepted": False, "reason": reason, "critique": critique})
            _save_state(out, st)
            return {"ok": False, "reason": reason, "critique": critique, "results": results, "step": st["step"]}
        shutil.copyfile(Path(t) / "next.designcraft", _file(out, step, "designcraft"))
        shutil.copyfile(Path(t) / "next.pdf", _file(out, step, "pdf"))
    _commit(out, files, new_scenes, st, step, {**entry, "accepted": True})
    return {"ok": True, "step": step, "results": results, "changed": diff, "fixed_issues": entry["fixed_issues"],
            "document": str(_file(out, step, "designcraft")), "pdf": str(_file(out, step, "pdf"))}


def _commit(out, files, scenes, st, step, entry):
    _file(out, step, "scenes.json").write_text(json.dumps(scenes, ensure_ascii=False), encoding="utf-8")
    for f, sc in zip(files, scenes):
        f.write_text(json.dumps(sc, indent=1, ensure_ascii=False), encoding="utf-8")
    st["step"] = step
    st["history"].append(entry)
    _save_state(out, st)


def sync(out_dir, document):
    """The user saved `document` from the editor. Their changes become the next step and are marked as theirs.
    Gate issues are reported, never a reason to refuse: the user owns the page."""
    out, run, manifest, files, scenes, measurer = _load(out_dir)
    dc, st = _dc(), _state(out)
    if st is None:
        return {"ok": False, "reason": "NO_LIVE_SESSION"}
    theirs = dc.read(document)
    diff = dc.changed(dc.read(_file(out, st["step"], "designcraft")), theirs)
    if not diff:
        return {"ok": True, "step": st["step"], "changed": {}}
    step = st["step"] + 1
    shutil.copyfile(document, _file(out, step, "designcraft"))
    new_scenes = _merge(scenes, theirs, "user", set(diff))
    issues = [{"page": p, "code": c, "elements": list(e), "details": d} for (p, c, e), d in _blocking(new_scenes, manifest, run["spec"], measurer).items()]
    _commit(out, files, new_scenes, st, step, {"step": step, "by": "user", "changed": diff, "accepted": True})
    return {"ok": True, "step": step, "changed": diff, "blocking_issues": issues, "user_objects": sorted(k for k in diff if k.startswith("user:"))}


def undo(out_dir):
    """One step back. The files of the step that was undone stay on disk; the next accepted edit writes over that number."""
    out, run, manifest, files, scenes, measurer = _load(out_dir)
    st = _state(out)
    if st is None or st["step"] == 0:
        return {"ok": False, "reason": "NOTHING_TO_UNDO"}
    step = st["step"] - 1
    old = json.loads(_file(out, step, "scenes.json").read_text(encoding="utf-8"))
    _commit(out, files, old, st, step, {"step": step, "by": "undo", "accepted": True})
    return {"ok": True, "step": step, "document": str(_file(out, step, "designcraft"))}
