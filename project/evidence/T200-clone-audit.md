# T200/T216 evidence — pinned clone + static audit (2026-11-04, Windows 11, git via Git Bash)
- `python scripts/clone_repos.py --apply` (log: evidence/logs/T216-clone-apply.txt): 27/27 repos at pinned SHA (ALREADY_PINNED 22 + CHECKOUT_PINNED 5), 0 failures. First run was interrupted by a full disk; rerun resumed idempotently, existing clones SHA-verified.
- `python scripts/audit_repos.py` -> evidence/T200-repo-audit.json: independent `git rev-parse HEAD` == lock SHA for all 27 (exit 0).
- Negative: existing clone dir with a different HEAD -> clone_repos refuses to overwrite, exit!=0 ("Refusing to overwrite existing repo ... expected <sha>").
- Evidence label: CODE_INSPECTED (static: license header, manifests, tests dir). Nothing from any clone was installed or executed (REPRODUCED = none yet).
- License heuristics (header-based, must be confirmed by hand in T210): AGPL-3.0 = vivliostyle (do not link/bundle); GPL-2.0 = scribus (process-isolated use only); MPL-2.0 = penpot; NO LICENSE FILE = paper2poster, slidesgen-bench, deckbench (code-reuse not permitted without grant; read/measure only). DesignCraft family/HarnessRouter CE/GenOffice = Apache-2.0; OpenPencil, AutoDesign, DeepSlides, diagram-design = MIT.
- Toolchain gap: no cargo/rustc on host -> the Rust *Craft backends (T212/T213/T408) cannot build until Rust is installed (needs approval, network + disk).

## CORRECTION (2026-11-04, later)
The first audit only compared HEAD SHA. After the disk-full interruption, `paper2poster` and `pagedjs` had HEAD at the pinned SHA but an EMPTY/incomplete working tree (1793/797 staged deletions), so "27/27 OK" was overstated. Fixed with `core.longpaths=true` + sparse-checkout excluding `assets/poster_data/` (paper2poster, large train data, Windows long paths) and `specs/**/__image_snapshots__/` (pagedjs). audit_repos.py now also requires a clean worktree. These two clones are therefore PARTIAL by design (excluded dirs listed above).
