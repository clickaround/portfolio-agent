# runtime/

`portfolio_agent/` = orchestration + local compositor (ingest, pattern retrieval, plan, layout, QA, repair, edit, candidates), implemented under ADR-0007 as candidate D / fallback.
Backend-specific adapters live in `backends/<name>/`. Not the chosen architecture; see architecture/adr/0007-local-compositor-is-a-candidate.md.
