"""C8 hook (gitagent `pre_tool_use`): block a tool call that breaks a guardrail the prompt cannot guarantee.

gitagent gives the event as one JSON object on stdin and reads the answer from stdout
(open-gitagent/gitagent, crates/hooks/src/lifecycle.rs):
  in   {"event": "pre_tool_use", "tool": "write", "args": {...}, "data": {"tool_name": ..., "arguments": {...}}}
  out  {"action": "allow"}  or  {"action": "block", "reason": "..."}

The rules are data, in ../guard.json next to hooks.yaml:
  {"deny": [{"tools": ["write", "edit"], "pattern": "<regex>", "rule": "GUARDRAILS 1", "reason": "..."}]}
`tools` uses the gitagent 1.x names (cli, read, write, edit, ...); the pattern is searched in the call's
arguments as JSON text, with backslashes turned into slashes. Standard library only.

This file is the same in every agent; baseAgent/scripts/render_host.py copies it from baseAgent.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RULES = Path(__file__).resolve().parents[1] / "guard.json"


def decide(event: dict, rules: dict) -> dict:
    data = event.get("data") or {}
    tool = event.get("tool") or data.get("tool_name") or ""
    args = event.get("args") or data.get("arguments") or {}
    text = json.dumps(args, ensure_ascii=False).replace("\\\\", "/")
    for rule in rules.get("deny", []):
        if tool in rule["tools"] and re.search(rule["pattern"], text):
            return {"action": "block", "reason": f"{rule['rule']}: {rule['reason']}"}
    return {"action": "allow"}


def main() -> int:
    try:
        event = json.loads(sys.stdin.read() or "{}")
        rules = json.loads(RULES.read_text(encoding="utf-8"))
        answer = decide(event, rules)
    except (ValueError, OSError, KeyError, re.error) as exc:
        # hooks.yaml registers this hook with fail_open: false, so a broken guard blocks instead of passing silently.
        print(f"guard.py failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(answer))
    return 0


if __name__ == "__main__":
    sys.exit(main())
