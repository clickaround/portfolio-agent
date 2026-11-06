#!/usr/bin/env python3
"""Read-only static audit of pinned clones: SHA match, license file, manifests. Executes nothing from clones."""
import sys, json, subprocess, re
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parent.parent
V = ROOT / ".cache/vendor"
LIC = [("Apache-2.0", r"Apache License"), ("MIT", r"Permission is hereby granted, free of charge"), ("AGPL-3.0", r"GNU AFFERO"), ("GPL-3.0", r"GNU GENERAL PUBLIC LICENSE\s+Version 3"), ("GPL-2.0", r"GNU GENERAL PUBLIC LICENSE\s+Version 2"), ("LGPL", r"GNU LESSER"), ("MPL-2.0", r"Mozilla Public License"), ("BSD", r"Redistribution and use in source and binary forms"), ("Unlicense", r"unlicense")]
MAN = ["package.json", "Cargo.toml", "pyproject.toml", "requirements.txt", "setup.py", "go.mod", "Dockerfile", "CMakeLists.txt"]
rows = []
for r in json.loads((ROOT / "research/repos.lock.json").read_text(encoding="utf-8"))["repositories"]:
    p = V / r["id"]; row = {"id": r["id"], "pinned": r["sha"][:10], "group": r.get("group")}
    if not p.is_dir(): row.update(sha_ok=False, note="not cloned"); rows.append(row); continue
    head = subprocess.run(["git", "-C", str(p), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    row["sha_ok"] = head == r["sha"]
    st = subprocess.run(["git", "-C", str(p), "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
    row["worktree_clean"] = st == ""; row["tracked_files"] = len(subprocess.run(["git", "-C", str(p), "ls-files"], capture_output=True, text=True).stdout.splitlines())
    lf = next((f for f in p.iterdir() if re.match(r"(LICENSE|LICENCE|COPYING)", f.name, re.I) and f.is_file()), None)
    if lf:
        t = lf.read_text(encoding="utf-8", errors="replace")[:6000]
        row["license"] = next((n for n, rx in LIC if re.search(rx, t[:400], re.I)), None) or next((n for n, rx in LIC if re.search(rx, t, re.I)), "UNRECOGNIZED:" + lf.name)
    else: row["license"] = "NO_LICENSE_FILE"
    row["manifests"] = [m for m in MAN if (p / m).exists()]
    row["has_tests_dir"] = any((p / d).is_dir() for d in ("tests", "test", "__tests__"))
    row["evidence"] = "CODE_INSPECTED(static); NOT executed"
    rows.append(row)
out = ROOT / "evidence/T200-repo-audit.json"; out.write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")
for x in rows: print(x["id"].ljust(24), "sha_ok=%s clean=%s files=%s" % (x["sha_ok"], x.get("worktree_clean"), x.get("tracked_files")), str(x.get("license")).ljust(22), ",".join(x.get("manifests", [])), "tests" if x.get("has_tests_dir") else "")
sys.exit(0 if all(x["sha_ok"] and x.get("worktree_clean") for x in rows) else 1)
