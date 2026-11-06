# T002 evidence — Codex host
- `codex --version` = codex-cli 0.166.0 (log: evidence/logs/T002-codex.txt)
- Official CLI syntax recorded: `codex plugin {add,list,marketplace,remove}`; `codex plugin add` installs from a configured/remote marketplace; `codex mcp` manages MCP servers.
- .codex-plugin/plugin.json exists (name, version, skills ./skills/, interface). Codex has no `validate` subcommand, so manifest acceptance is UNVERIFIED.
- NOT run: `codex plugin marketplace add <local path>` / `plugin add` (modifies ~/.codex config; needs user approval). Next step if approved: add local marketplace, `codex plugin list`, confirm portfolio-agent appears.
