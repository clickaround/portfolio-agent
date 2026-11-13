"""C7 script: run one command of the project's CLI as a gitagent script tool.

gitagent starts a declared tool (tools/<name>.yaml -> its launcher tools/<name>.sh) with the call's
arguments as ONE JSON object on stdin. A CLI takes argv. Each launcher runs

    python scripts/tool_entry.py <cli command> [<positional argument name> ...]

Arguments named there are passed by position; every other argument becomes `--flag value` (true -> bare flag).

Which CLI is the agent's own setting, in tools/cli.json:

    {"module": "my_package.cli", "function": "main", "console_script": "my-cli"}

`module:function` is called with the argv list. When the module cannot be imported in the launcher's
python, `console_script` is run through `uv run` at the nearest parent folder that has a uv.lock.

This file is the same in every agent; baseAgent/scripts/render_host.py copies it from baseAgent.
"""
from __future__ import annotations

import importlib
import json
import subprocess
import sys
from pathlib import Path

CLI = Path(__file__).resolve().parents[1] / "tools" / "cli.json"


def to_argv(command: str, positional: list[str], args: dict) -> list[str]:
    """`{"project": "p", "width_mm": 297, "approve": true}` -> `[command, "p", "--width-mm", "297", "--approve"]`."""
    missing = [name for name in positional if name not in args]
    if missing:
        raise ValueError(f"{command}: missing required argument(s): {', '.join(missing)}")
    argv = [command] + [str(args[name]) for name in positional]
    for name, value in args.items():
        if name in positional or value is None or value is False:
            continue
        flag = "--" + name.replace("_", "-")
        argv += [flag] if value is True else [flag, str(value)]
    return argv


def workspace_root() -> Path | None:
    """The nearest parent folder that holds `uv.lock`."""
    for parent in Path(__file__).resolve().parents:
        if (parent / "uv.lock").is_file():
            return parent
    return None


def fail(message: str) -> int:
    print(json.dumps({"ok": False, "error": message}))
    return 2


def run(command: str, positional: list[str]) -> int:
    raw = sys.stdin.read().strip()
    try:
        args = json.loads(raw) if raw else {}
        if not isinstance(args, dict):
            raise ValueError("arguments must be one JSON object")
        argv = to_argv(command, positional, args)
        cli = json.loads(CLI.read_text(encoding="utf-8"))
        module, function, script = cli["module"], cli.get("function", "main"), cli.get("console_script")
    except OSError:
        return fail(f"{CLI.name} is missing next to the tool; it names the CLI this agent's tools run")
    except (ValueError, KeyError) as exc:
        return fail(str(exc))
    try:
        main = getattr(importlib.import_module(module), function)
    except ImportError:
        root = workspace_root()
        if not script or root is None:
            return fail(f"{module} cannot be imported in this python and there is no console_script or uv workspace to fall back to")
        try:
            # --project selects the workspace environment; the caller's working directory (and its relative paths) is kept.
            return subprocess.run(["uv", "run", "--project", str(root), script, *argv], check=False).returncode
        except FileNotFoundError:
            return fail(f"{module} cannot be imported in this python and `uv` is not on PATH")
    return main(argv) or 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(run(sys.argv[1], sys.argv[2:]))
