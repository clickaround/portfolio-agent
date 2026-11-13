"""Enforces the layering (backend/common/ARCHITECTURE.md; the Python analogue of DesignCraft's `cargo xtask layers`) across ALL source roots
of the portfolio_agent namespace package, and the workspace folder rules (agents / backend / frontend / project).

    core (backend/common)  <-  layout  <-  authors/*, backends/*  <-  engine (portfolioAgent + sourcePrepAgent + reviewAgent)  <-  cli
"""
import ast
import unittest
from pathlib import Path

from portfolio_agent.core.workspace import WORKSPACE

SOURCE_ROOTS = [WORKSPACE / "backend" / "packages" / "portfolio-core" / "src", *sorted((WORKSPACE / "agents").glob("*Agent/src"))]
AGENTS = WORKSPACE / "agents"
BACKENDS = AGENTS / "portfolioAgent" / "backends"
TOP_LEVEL_ALLOWED = {
    "agents", "backend", "frontend", "editor", "project", "supabase",  # documented product folders
    "_bmad", "_bmad-output",                              # BMAD planning tool output
    ".agents", ".cache", ".git", ".github", ".remember", ".pytest_cache", ".claude", ".vscode", ".idea", ".venv", ".ruff_cache", ".import_linter_cache", ".playwright-mcp",
}
NAMESPACE_DIRS = {"portfolio_agent", "engine"}            # PEP 420: spread over several agents, so no __init__.py


def imports_of(path, module_name):
    """All absolute module names imported by `path` (relative imports resolved against module_name)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    pkg_parts = module_name.split(".")[:-1] if path.name != "__init__.py" else module_name.split(".")
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            out += [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            if n.level:
                base = pkg_parts[: len(pkg_parts) - (n.level - 1)]
                mod = ".".join(base + ([n.module] if n.module else []))
                out.append(mod)
                out += [mod + "." + a.name for a in n.names]
            elif n.module:
                out.append(n.module)
                out += [n.module + "." + a.name for a in n.names]
    return out


def package_modules():
    for root in SOURCE_ROOTS:
        pkg = root / "portfolio_agent"
        if not pkg.is_dir():
            continue
        for p in sorted(pkg.rglob("*.py")):
            rel = p.relative_to(root).with_suffix("")
            parts = list(rel.parts)
            if parts[-1] == "__init__":
                parts = parts[:-1]
            yield p, ".".join(parts)


def layer_of(mod):
    if mod.startswith("portfolio_agent.core"):
        return "core"
    if mod.startswith("portfolio_agent.layout"):
        return "layout"
    if mod.startswith("portfolio_agent.authors"):
        return "authors"
    if mod.startswith("portfolio_agent.engine"):
        return "engine"
    if mod == "portfolio_agent.cli":
        return "cli"
    return None


class LayeringTests(unittest.TestCase):
    def violations(self, layer, forbidden, extra=None):
        bad = []
        for p, mod in package_modules():
            if layer_of(mod) != layer:
                continue
            for imp in imports_of(p, mod):
                tgt = layer_of(imp)
                if tgt in forbidden or (extra and extra(mod, imp)):
                    bad.append(f"{mod} imports {imp}")
        return bad

    def test_core_imports_no_other_layer(self):
        self.assertEqual(self.violations("core", {"layout", "authors", "engine", "cli"}), [])

    def test_layout_imports_only_core(self):
        self.assertEqual(self.violations("layout", {"authors", "engine", "cli"}), [])

    def test_authors_import_only_core_and_never_each_other(self):
        def cross_author(mod, imp):
            a, b = mod.split(".")[2:3], imp.split(".")[2:3]
            return imp.startswith("portfolio_agent.authors.") and mod.startswith("portfolio_agent.authors.") and a and b and a != b and a[0] not in ("knowledge",) and b[0] not in ("knowledge",)
        self.assertEqual(self.violations("authors", {"engine", "cli"}, cross_author), [])

    def test_engine_does_not_import_cli_and_only_registry_imports_authors(self):
        def authors_outside_registry(mod, imp):
            return imp.startswith("portfolio_agent.authors") and not mod.endswith("engine.registry")
        self.assertEqual(self.violations("engine", {"cli"}, authors_outside_registry), [])

    def test_cli_talks_to_engine_only(self):
        self.assertEqual(self.violations("cli", {"core", "authors"}), [])

    def test_backends_import_only_core_of_the_package(self):
        bad = []
        for adapter in sorted(BACKENDS.glob("*/adapter.py")):
            for imp in imports_of(adapter, f"pa_backend_{adapter.parent.name}"):
                if imp.startswith("portfolio_agent") and layer_of(imp) not in ("core",) and imp != "portfolio_agent":
                    bad.append(f"{adapter.parent.name} imports {imp}")
                if imp.startswith("pa_backend_"):
                    bad.append(f"{adapter.parent.name} imports another backend {imp}")
        self.assertEqual(bad, [])

    def test_every_backend_exposes_BACKEND_with_declared_capabilities(self):
        from importlib import util
        for adapter in sorted(BACKENDS.glob("*/adapter.py")):
            src = adapter.read_text(encoding="utf-8")
            self.assertIn("BACKEND =", src, adapter)
            self.assertIn("capabilities", src, adapter)


class AgentFolderTests(unittest.TestCase):
    def test_source_prep_and_review_agents_import_only_core(self):
        bad = []
        for agent in ("sourcePrepAgent", "reviewAgent"):
            for p in sorted((AGENTS / agent / "src").rglob("*.py")):
                mod = ".".join(p.relative_to(AGENTS / agent / "src").with_suffix("").parts)
                for imp in imports_of(p, mod):
                    if imp.startswith("portfolio_agent") and layer_of(imp) not in ("core", None):
                        bad.append(f"{agent}: {mod} imports {imp}")
        self.assertEqual(bad, [], "sourcePrepAgent / reviewAgent depend on backend/common (core) only, never on portfolioAgent")

    def test_agent_folders_are_self_describing(self):
        for agent in ("portfolioAgent", "sourcePrepAgent", "reviewAgent"):
            self.assertTrue((AGENTS / agent / "AGENTS.md").is_file(), f"{agent}/AGENTS.md (identity, contract, how to test) is required")
            self.assertTrue((AGENTS / agent / "tests").is_dir(), f"{agent}/tests")

    def test_base_agent_module_has_the_eight_harness_components(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("check_base", AGENTS / "baseAgent" / "scripts" / "check_base.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertEqual(mod.check(AGENTS / "baseAgent"), [], "agents/baseAgent is the gitagent + Harness² base every agent folder is copied from")
        for agent in ("portfolioAgent", "sourcePrepAgent", "reviewAgent"):
            self.assertEqual(mod.check(AGENTS / agent), [], f"{agent} must follow agents/baseAgent (gitagent names + Harness² C1..C8)")

    def test_host_skills_are_rendered_from_the_owning_agent(self):
        import subprocess, sys
        r = subprocess.run([sys.executable, str(AGENTS / "baseAgent" / "scripts" / "render_host.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, "agents/<agent>/skills/ is the source; run agents/baseAgent/scripts/render_host.py: " + r.stdout)

    def test_agent_tools_declare_real_cli_subcommands(self):
        import re
        cli = (AGENTS / "portfolioAgent" / "src" / "portfolio_agent" / "cli.py").read_text(encoding="utf-8")
        for path in sorted(AGENTS.glob("*Agent/tools/*.yaml")):
            sub = re.search(r'tool_entry\.py" ([\w-]+)', path.with_suffix(".sh").read_text(encoding="utf-8")).group(1)   # the launcher names the CLI subcommand
            self.assertIn(f'add_parser("{sub}")', cli, f"{path.parent.parent.name}/tools/{path.name} declares a CLI command that does not exist")


    def test_a_declared_tool_runs_from_json_on_stdin(self):
        """gitagent hands a script tool its arguments as one JSON object on stdin: 2.x runs `sh tools/<x>.sh` in the agent folder."""
        import json, shutil, subprocess
        if not shutil.which("sh"):
            self.skipTest("sh is not on PATH (gitagent starts hooks and these tools with sh)")
        tools = AGENTS / "portfolioAgent"
        project = AGENTS / "portfolioAgent" / "examples" / "synthetic_projects" / "photo_01"
        ok = subprocess.run(["sh", "tools/manifest.sh"], cwd=tools, input=json.dumps({"project": str(project)}), capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertEqual(json.loads(ok.stdout)["project_id"], "photo_01")
        bad = subprocess.run(["sh", "tools/manifest.sh"], cwd=tools, input="{}", capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(bad.returncode, 2)
        self.assertIn("missing required argument", bad.stdout)

    def test_guard_hooks_block_what_the_guardrails_forbid(self):
        """C8: each agent's pre_tool_use hook, run the way gitagent 2.x runs it: `sh <script>` with the event JSON on stdin."""
        import json, shutil, subprocess
        if not shutil.which("sh"):
            self.skipTest("sh is not on PATH (gitagent starts hooks with sh)")

        def ask(agent, tool, args):
            event = {"event": "pre_tool_use", "tool": tool, "args": args, "data": {"tool_name": tool, "arguments": args}}
            r = subprocess.run(["sh", "hooks/scripts/guard.sh"], cwd=AGENTS / agent, input=json.dumps(event), capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            return json.loads(r.stdout)["action"]

        for agent in ("sourcePrepAgent", "portfolioAgent"):
            self.assertEqual(ask(agent, "write", {"path": "proj\\sources\\a.jpg"}), "block", "originals are never overwritten")
            self.assertEqual(ask(agent, "cli", {"command": "rm -rf proj/sources/a.jpg"}), "block")
            self.assertEqual(ask(agent, "cli", {"command": "cat x > proj/sources/a.jpg"}), "block")
            self.assertEqual(ask(agent, "read", {"path": "proj/sources/a.jpg"}), "allow", "reading an original is fine")
            self.assertEqual(ask(agent, "write", {"path": "proj/images/a.png"}), "allow")
            self.assertEqual(ask(agent, "read", {"path": ".cache/_unblind_key_3.json"}), "block", "a generating agent never sees the unblind key")
        self.assertEqual(ask("reviewAgent", "write", {"path": "out/final/book.pdf"}), "block", "only finalize promotes to final/")
        self.assertEqual(ask("reviewAgent", "cli", {"command": "cp out/attempts/01/book.pdf out/final/"}), "block")
        self.assertEqual(ask("reviewAgent", "write", {"path": "out/attempts/01/review.json"}), "allow")
        self.assertEqual(ask("reviewAgent/agents/fresh-reviewer", "read", {"path": ".cache/_unblind_key.json"}), "block")
        self.assertEqual(ask("reviewAgent/agents/fresh-reviewer", "read", {"path": "out/preview/page-01.png"}), "allow")
        broken = subprocess.run(["sh", "hooks/scripts/guard.sh"], cwd=AGENTS / "reviewAgent", input="not json", capture_output=True, text=True)
        self.assertNotEqual(broken.returncode, 0, "a guard that cannot read its event fails, and hooks.yaml sets fail_open: false")

    def test_tool_arguments_become_cli_arguments(self):
        import sys
        sys.path.insert(0, str(AGENTS / "baseAgent" / "scripts"))
        from tool_entry import to_argv  # noqa: E402
        self.assertEqual(
            to_argv("compose", ["project", "plan", "out"], {"out": "o", "project": "p", "plan": "b.json", "width_mm": 297, "design_plan": None}),
            ["compose", "p", "b.json", "o", "--width-mm", "297"])
        self.assertEqual(to_argv("prepare", ["project"], {"project": "p", "approve": True, "levels": False}), ["prepare", "p", "--approve"])

    def test_the_folder_checker_rejects_a_broken_agent_folder(self):
        import importlib.util, shutil, tempfile
        spec = importlib.util.spec_from_file_location("check_base", AGENTS / "baseAgent" / "scripts" / "check_base.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "reviewAgent"
            shutil.copytree(AGENTS / "reviewAgent", copy, ignore=shutil.ignore_patterns("src", "tests", "benchmarks", "__pycache__", ".pytest_cache"))
            self.assertEqual(mod.check(copy), [])
            (copy / "agents" / "fresh-reviewer" / "SOUL.md").unlink()                      # sub-agent without identity
            (copy / "tools" / "finalize.sh").unlink()                                      # tool without its launcher
            manifest = copy / "agent.yaml"
            manifest.write_text(manifest.read_text(encoding="utf-8").replace("  - portfolio-review\n", ""), encoding="utf-8")   # skill not listed
            (copy / "guardrails" / "GUARDRAILS.md").write_text('"verdict": "pass"\n', encoding="utf-8")                        # grader output
            problems = "\n".join(mod.check(copy))
        for expected in ("fresh-reviewer/SOUL.md", "finalize.sh", "portfolio-review", "grader-output marker"):
            self.assertIn(expected, problems)


class FolderTests(unittest.TestCase):
    def test_top_level_folders_are_documented(self):
        actual = {p.name for p in WORKSPACE.iterdir() if p.is_dir() and any(p.iterdir())}   # an empty leftover dir (locked by an editor on Windows) is harmless
        self.assertEqual(sorted(actual - TOP_LEVEL_ALLOWED), [], "new top-level folder: document it and update the workspace folder rule")
        self.assertIn("`editor/`", (WORKSPACE / "README.md").read_text(encoding="utf-8"))

    def test_every_package_dir_has_init_except_namespace_dirs(self):
        missing = []
        for root in SOURCE_ROOTS:
            pkg = root / "portfolio_agent"
            if not pkg.is_dir():
                continue
            for d in [pkg, *pkg.rglob("*")]:
                if d.is_dir() and d.name != "__pycache__" and any(d.glob("*.py")) and not (d / "__init__.py").exists() and d.name not in NAMESPACE_DIRS:
                    missing.append(str(d.relative_to(WORKSPACE)))
        self.assertEqual(missing, [])

    def test_no_namespace_dir_has_init(self):
        bad = [str(root / "portfolio_agent" / n) for root in SOURCE_ROOTS for n in ("", "engine") if (root / "portfolio_agent" / n / "__init__.py").exists()]
        self.assertEqual(bad, [], "portfolio_agent and portfolio_agent.engine are PEP 420 namespaces: an __init__.py would hide the other agents' modules")

    def test_no_data_files_inside_source_roots(self):
        data = [str(p.relative_to(WORKSPACE)) for root in SOURCE_ROOTS for p in root.rglob("*") if p.is_file() and p.suffix in (".json", ".csv", ".txt") and "__pycache__" not in p.parts and "schemas" not in p.parts]
        self.assertEqual(data, [], "data belongs in knowledge/ - only the JSON schemas (core/schemas) ship inside the kernel")


class DetectorSelfTest(unittest.TestCase):
    """The layering check must actually fail on a violation (negative test)."""

    def test_detects_core_importing_engine_and_relative_imports(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "bad.py"
            f.write_text(chr(10).join(["from portfolio_agent.engine import pipeline", "from ..engine import registry", "import os", ""]), encoding="utf-8")
            imps = imports_of(f, "portfolio_agent.core.bad")
            self.assertIn("portfolio_agent.engine", imps)
            self.assertIn("portfolio_agent.engine.registry", imps)
            self.assertEqual({layer_of(i) for i in imps if layer_of(i)}, {"engine"})


if __name__ == "__main__":
    unittest.main()
