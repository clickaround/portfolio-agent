# DesignCraft backend spike (2026-11-04, Windows 11) — REPRODUCED (single run, synthetic assets)
- Binary: official release v0.17.0 `designcraft-0.17.0-windows-x64-portable.zip` (124,340,370 B). SHA256 37dd157b7af22864e4d2693e60411c5e5cce492d69042bf03af8728f8b7f8134 == release SHA256SUMS.txt. Both exes Authenticode `Valid`, signer "Learning Machines Inc". License Apache-2.0 (+MIT, OFL fonts). User approved download/run 2026-11-04. Run only from .cache/bin/designcraft, headless CLI, no network used by us.
- `designcraft-cli --version` = 0.17.0; `commands` lists ~450 commands; `script` takes one `command {json}` per line, `$N.id` refs are 0-based step indexes; file.new width/height are POINTS (297 treated as pt first try -> 104.8 mm page: wrong until converted).
- Adapter: runtime/portfolio_agent/backend_designcraft.py (scene mm -> script). Run on our 5-page arch_01 scenes: exit 0; produced .designcraft, PDF, IDML, PPTX (file existence verified).
- PDF checks (PyMuPDF): 5 pages 297x210 mm exact; text extractable on all pages; raster images placed; synthetic plan PDF keeps vector linework (63 drawing ops on p3); real text with embedded fonts.
- Visual: same composition as our own renderer; typography engine differs (serif default, Knuth-Plass breaks, hyphenation "Hous-ing" on the cover is ugly -> need fontFamily + hyphenation off style).
- NOT verified: opening .idml in InDesign; PPTX fidelity/opening in PowerPoint; local-edit preservation inside DesignCraft; MCP server session; GUI app; fonts (Korean glyph coverage of the default family); shapes (rule drawn with default stroke, fill/stroke params not set); styles for color/alignment.
- Limits: tuned only on one project; script is regenerated from scenes, not a round-trip editor.

## MCP (REPRODUCED)
`designcraft-cli mcp --automation-read-root <examples> --automation-write-root C:/DK/dc_work` over stdio JSON-RPC (protocol 2025-06-18): initialize -> serverInfo designcraft 0.17.0; tools/list = 26 tools (list_commands, execute, batch, inspect_document, get_story, set_story_text, new_document, open_document, save_document, place_image, render_page, export_png, screenshot, ...); `execute file.new` OK; `save_document` to C:/Windows/Temp is REJECTED ("automation path rejected: outside the write root") -> root confinement works for that path. Not tested: read-root confinement, symlink escape, prompt-injection via document text.
## T212 scope note
Satisfied by the signed release binary (no Rust/cargo needed). Building from source with Rust was NOT tested (no cargo on this host).
