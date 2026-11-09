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


def make_read_only_claude_runner(claude_bin: str = "claude") -> Runner:
    """Text-only analysis: disable built-in tools, and ignore project plugins/settings."""
    def run(prompt: str, cwd: Path, timeout_s: int, allowed_tools: str = ""):
        if allowed_tools != "":
            raise ValueError("Analysis runner does not allow tools")
        p = subprocess.run([claude_bin, "-p", "--restricted", "--tools", "",
                            "--permission-prompts", "none", "--output-format", "text"], cwd=str(cwd), capture_output=True,
                           text=True, encoding="utf-8", errors="replace", timeout=timeout_s, input=prompt)
        if p.returncode != 0 and any(marker in (p.stdout + p.stderr).lower() for marker in ("weekly limit", "usage limit")):
            return p.returncode, "CLAUDE_USAGE_LIMIT"
        return p.returncode, p.stdout if p.returncode == 0 else p.stderr
    return run
