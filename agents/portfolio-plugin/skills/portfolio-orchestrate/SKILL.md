---
name: portfolio-orchestrate
description: Delegate independent portfolio tasks across agents with typed evidence handoffs and single document writer.
---
# Portfolio Orchestrate

Multi-agent is optional; prefer one integration lead and max two independent specialists when tasks truly parallelize. Read `agents/WORKSHARE.md`, schema, backlog DAG and the current task card. Assign disjoint paths/worktrees. Research, case annotation and backend audit can run concurrently; writing to same source/Scene document cannot. Specialists return structured result files using `agents/contracts/task-result.schema.json`; integration lead reviews, runs tests, updates `../../project/tasks/backlog.json`, memory and ADRs. Use HarnessRouter only if direct Codex/Claude runs already work and unified external task orchestration is warranted.
