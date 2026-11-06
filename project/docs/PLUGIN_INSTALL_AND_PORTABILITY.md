# Multi-host packaging check (NOT VERIFIED BY PACKAGE GENERATION)

- Portable plugin: root `plugin.json` + `skills/<name>/SKILL.md`; Codex-specific metadata under `.codex-plugin/`; Claude-specific manifest under `.claude-plugin/` and marketplace JSON. These are scaffolds; validate against **installed host version** and official schemas.
- Claude Code: read `AGENTS.md` via `CLAUDE.md` import, then validate local plugin with available host CLI. Do not assume every release exposes identical commands.
- Codex: test local discovery and marketplace registration separately. A valid JSON manifest is not successful plugin activation.
- Shared Skills must not assume external MCP server installed. Backends are optional and auto-discovered. Unknown backend → clear failure/fallback, not fake output.
- No API secrets in repository. Host plugin subscriptions/usage terms may differ; integration scripts don't grant paid entitlements.
