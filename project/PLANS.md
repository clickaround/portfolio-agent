# Master plan / dependency gates (v0.4.0)

`tasks/backlog.json` is the single authoritative task DAG and each `tasks/cards/Txxx.md` is an executable contract. `memory/NOW.md` is a pointer, not a second task database. Run `python scripts/task_status.py --ready` before assigning work. Do not mark tasks completed based on this package's existing test output.

| Phase | Outcome | Exit gate |
|---|---|---|
| P00 | Host discovery + package sanity | Static checks pass; host states precisely REPRODUCED/BLOCKED |
| P01 | Portfolio semantics & cases | Taxonomy, rights-aware reference selection, at least synthetic fixtures and benchmark split plan |
| P02 | Repository auto-clone & audit | Pinned clones / logs or explicit blockers, legal status, reproducible smoke plan |
| P03 | Format contract & architecture alternatives | Native sizes/print specs, core data contracts, independent review |
| P04 | Backend spikes (DesignCraft / OpenPencil / GenOffice / fallback) | At least one candidate tested end to end, negative source-fidelity fixtures |
| P05 | Independent benchmark design | deterministic validity, blind preference, reference and domain ablations, untrained baseline |
| P06 | Thin end-to-end plugin prototype | two pages, arbitrary page format, user images, editable source and PDF |
| P07 | Multidomain & multiformat extensions | separate domains and at least 2 meaningful formats; no hardcoded architecture assumptions |
| P08 | Controlled multi-agent workflow | schema-based handoffs, single-writer merge, direct host comparison |
| P09 | Optional HarnessRouter / training / commercialization | isolation, costs, licenses and business evidence; *never automatically required* |

## Work scheduling
Independent **case/reference research** and **source/backend code audits** may run in parallel after P00. Backends should be compared as alternatives; their failures cannot block a working fallback. If no authorized portfolio sample is available, use synthetic data to continue engine development, but mark the real-case quality gate `BLOCKED`—never mislabel synthetic data as professional-quality evidence.

## Role split
Integration Lead owns shared task statuses/memory/ADRs; a research agent and a design/QA specialist may work in separate branches/worktrees under `project/agent-roles/WORKSHARE.md`. Keep small PRs/changes, one artifact owner. Do not have multiple agents share writes to a Scene Document or run competing DB migrations.

## Exit evidence
`evidence/<phase>/<task-id>.md` with hypothesis, exact pinned versions, commands and return codes, hashes, measured outputs, failures, next step. A failed experiment is acceptable evidence for rejecting a backend, not a pass. No promised background execution.
