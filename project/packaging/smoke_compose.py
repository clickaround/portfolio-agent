"""Check the installed wheel bundle using synthetic data, without the checkout on sys.path."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image
from portfolio_agent.core import workspace

if not workspace._installed:
    raise SystemExit("Run from outside the checkout using the isolated wheel environment")

with tempfile.TemporaryDirectory(prefix="portfolio-wheel-smoke-") as temp:
    root = Path(temp)
    source = root / "input"
    (source / "images").mkdir(parents=True)
    (source / "project.md").write_text("# Synthetic\n\n## Work\nSynthetic sample.\n", encoding="utf-8")
    Image.new("RGB", (640, 480), "#668899").save(source / "images" / "img01.png")
    plan = {"schema_version": "0.1.0", "doc_title": "Synthetic", "domain": "photography", "keywords": ["test"],
            "tokens": {}, "pages": [{"role": "cover", "assets": ["img01"], "title": "Synthetic"},
                                    {"role": "closing", "assets": [], "statement": "Synthetic test"}]}
    plan_path = root / "plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    env = os.environ.copy()
    env.pop("PASCAL_WORKSPACE", None)
    env["PASCAL_DATA_DIR"] = str(root / "userdata")
    command = [sys.executable, "-c", "from portfolio_agent.cli import main; raise SystemExit(main())", "compose",
               str(source), str(plan_path), str(root / "out")]
    result = subprocess.run(command, cwd=root, env=env, text=True, capture_output=True, check=True)
    summary = json.loads(result.stdout)
    if not summary.get("gate_pass") or not (root / "out" / "book.pdf").is_file():
        raise SystemExit(f"Compose output failed: {result.stdout} {result.stderr}")
    print(json.dumps({"synthetic": True, "gate_pass": summary["gate_pass"], "pages": summary["pages"]}))
