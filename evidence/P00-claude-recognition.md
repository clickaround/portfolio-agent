# T001 evidence — Claude Code host
- `claude --version` = 2.1.318 (Claude Code). Log: evidence/logs/T001-claude-validate.txt
- `claude plugin validate .` exit=0 "Validation passed with warnings" (plugin.json + marketplace.json + CLAUDE.md + agents checked).
- Findings (real, to fix): (1) agents/roles/*.md and agents/WORKSHARE.md have no YAML frontmatter -> Claude treats them as invalid agents; (2) no author, (3) no LICENSE/`license` (blocks directory submission; also T210 gate), (4) no icon.
- NOT run: `claude plugin install` into the user's profile (changes global state, needs user approval). Plugin *loading* in a live session is therefore UNVERIFIED; only manifest/static validity is verified.
