# Parallel agents/worktrees

Integrating agent owns `memory/`, `tasks/backlog.json`, `docs/adr/` and shared contracts; no one else edits those concurrently. Independent investigations may run in parallel without touching same paths:
- Portfolio domain/case expert T100–T109 → `research/domain/`, `cases/`.
- Repo/eval engineer T200–T211 → `research/`, `evidence/P02-*`.
- Evaluation metric engineer T300–T307 after prerequisites → `benchmarks/`, `contracts/` only if assigned.

A subagent returns an Evidence Packet (source/commit, inspected path or log, rights/license, failure, artifact hash, remaining unknown). Integration owner reviews conflicts and reruns validations. Do not parallelize tasks that both modify canonical memory, DAG, manifests, ADR or same native document.
