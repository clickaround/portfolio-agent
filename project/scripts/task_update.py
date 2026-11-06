#!/usr/bin/env python3
"""Integration-Lead-only task state writer. Refuses `done` without existing evidence file and PASS.
Usage: task_update.py T000 done --evidence evidence/P00-static.md [--pass PASS]
       task_update.py T001 blocked --reason "..."   """
import sys, json, argparse, datetime
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
B = ROOT / "tasks/backlog.json"
def main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("id"); p.add_argument("status", choices=["pending", "done", "blocked", "skipped"])
    p.add_argument("--evidence"); p.add_argument("--pass", dest="ps", default=None); p.add_argument("--reason"); p.add_argument("--waiver")
    a = p.parse_args(argv)
    d = json.loads(B.read_text(encoding="utf-8")); t = next((x for x in d["tasks"] if x["id"] == a.id), None)
    if not t: return print("UNKNOWN_TASK", a.id) or 2
    if a.status == "done":
        if not a.evidence or not (ROOT / a.evidence).is_file(): return print("REFUSED: evidence file missing") or 1
        if a.ps != "PASS": return print("REFUSED: done requires --pass PASS") or 1
        done = {x["id"] for x in d["tasks"] if x["status"] == "done" and x.get("pass_state") == "PASS"}
        if not set(t["dependencies"]) <= done: return print("REFUSED: dependencies not done", set(t["dependencies"]) - done) or 1
        t.update(status="done", pass_state="PASS", evidence_path=a.evidence, finished_at=datetime.datetime.now().astimezone().isoformat(timespec="seconds"))
    elif a.status in ("blocked", "skipped"):
        if not a.reason: return print("REFUSED: reason required") or 1
        if not a.evidence or not (ROOT / a.evidence).is_file(): return print("REFUSED: blocked/skipped also needs an existing --evidence file explaining it") or 1
        if a.status == "skipped" and not a.waiver: return print("REFUSED: skipped requires --waiver") or 1
        t.update(status=a.status, pass_state="BLOCKED" if a.status == "blocked" else "SKIPPED", evidence_path=a.evidence, finished_at=datetime.datetime.now().astimezone().isoformat(timespec="seconds"))
        if a.status == "blocked": t["blocked_reason"] = a.reason
        else: t["waiver"] = a.waiver
    else: t.update(status="pending", pass_state="UNVERIFIED")
    B.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"); print("OK", a.id, a.status); return 0
if __name__ == "__main__": sys.exit(main())
