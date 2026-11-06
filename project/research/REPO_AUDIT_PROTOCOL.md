# Auto clone → research → controlled reproduction

1. `python scripts/clone_repos.py --group layout` to preview exact targets.
2. `python scripts/clone_repos.py --id designcraft --apply` to clone a pinned public repository into `.cache/vendor/designcraft` (source only; does not install or run its code). The tool refuses unknown IDs and mismatched commits; may require Git and outbound network.
3. Before running tools inspect `LICENSE`, `NOTICE`, scripts, binary downloads, files read/write, network hooks, dependencies, documentation version, available tests and example input.
4. Create `research/reproductions/<id>.md`: commit, OS/tool versions, exact commands, exit codes, supplied rights-cleared inputs, screenshots and artifact hashes, limitations. **One tool in its own environment.**
5. Mark benchmark/commercial rights separately from source-code license.
6. If integration fails, document it and move to the declared alternative. Do not mark a successful smoke without an exit-code log and output artifact.
