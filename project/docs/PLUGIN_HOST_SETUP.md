# Plugin packaging/installation checks — version-specific

- Codex portable root manifest (`plugin.json`) + `skills/<name>/SKILL.md` follows https://developers.openai.com/plugins/build/plugins . For a **repo-local** marketplace, `.agents/plugins/marketplace.json` points `source.path: "./"` relative to the **repo marketplace root**, not to `.agents/plugins`. It must be verified in real host. Never say found based solely on JSON syntax.
- Claude native `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` follow https://code.claude.com/docs/en/plugins ; the repository root `CLAUDE.md` imports common `AGENTS.md`. Actual discovery/plugin validation is environment dependent.
- Skills here cover `portfolio-research`, `portfolio-plan`, `portfolio-review`, and `portfolio-experiment`. They **do not yet create a finished portfolio**; code-backed creation requires P04/P06.
- No MCP server is bundled in this v2 ZIP. Future MCP connects editor backends with user-authorized local subprocess/endpoint only.
- Host test must record `claude --version` / `codex --version`, plugin discovery or help commands actually available, any errors, whether `portfolio-plan` is invoked and the exact output. Do not propose commands as universally available without `--help` verification.
