# sourcePrepAgent Tool Guidance

<!-- Harness² C4 tool guidance (tool_descriptions/tool_guidance.md). Every call. When and how to use each existing tool. -->

- `prepare`: run first without `--approve` and look at the crop-proposal sheet. Add `--approve` only after the proposal is accepted. `--levels` for grey scans, `--knockout` when drawings must sit on a coloured page.
- `cutout`: only for subjects on a background that adds nothing (studio shots, model photos). Name the files. Default engine `rembg`; `photocraft` needs the signed binary in `.cache/bin`.
- Do not use either tool to fix layout problems; that belongs to portfolioAgent.
