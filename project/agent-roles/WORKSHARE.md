---
name: workshare
description: "Work-sharing rules for parallel portfolio-agent roles; Integration Lead is the only shared-state writer."
---
# Multi-agent workshare (optional, not required)

**Coordinator / Integration Lead**: sole owner of `tasks/backlog.json`, root instructions, `memory/`, ADR decisions and release packaging. Can assign parallel tasks only if the dependency DAG allows and file ownership does not collide.

Specialists:
- `case-curator`: pages, permissions, domain reference selection; owns only `cases/reviews/<taskid>/` and case report.
- `repo-auditor`: SHA, code, license, reproduction; owns only `research/reproductions/<taskid>/`.
- `domain-expert`: domain content/sequence rubric; owns only one `knowledge/domains/<domain>/` subtree per assignment.
- `layout-engineer`: medium-agnostic scene/layout, backends; owns a designated experiment directory.
- `quality-reviewer`: separate blind scoring and negative tests; writes to `benchmarks/reports/<taskid>/` only.

Start with one integrator + at most two concurrent specialists; independent research and technical spike can run concurrently. Use Git worktrees or separate branches. Never write the same Scene Document, shared task DAG, user source, or case license record from two workers. Reviewers must not silently change another agent's artifacts.

Handoff requires `project/agent-roles/contracts/task-result.schema.json` and `<task-id>.json`, plus the linked file evidence. Claims labeled DOC_REPORTED vs CODE_INSPECTED vs REPRODUCED.

Cancellation/failure: one specialist failure doesn't invalidate unrelated outputs; submit blocked report, coordinator may reassign. No automatic retries of expensive tools without budget.
