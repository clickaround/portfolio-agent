"""Host-LLM runner. The API never calls an Anthropic HTTP API (no billing): the book plan is written by the Claude Code CLI (`claude -p`) on the owner's
subscription, exactly like the terminal workflow. The runner is injectable so tests (and other hosts, e.g. Codex) can replace it."""
import subprocess
from collections.abc import Callable
from pathlib import Path

# runner(prompt, cwd, timeout_s, allowed_tools) -> (returncode, text)
Runner = Callable[[str, Path, int, str], tuple]


def make_claude_runner(claude_bin: str = "claude") -> Runner:
    def run(prompt: str, cwd: Path, timeout_s: int, allowed_tools: str = "Read,Write"):
        p = subprocess.run([claude_bin, "-p", prompt, "--allowedTools", allowed_tools, "--output-format", "text"], cwd=str(cwd), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout_s, stdin=subprocess.DEVNULL)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    return run
