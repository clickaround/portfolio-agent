# backend

`common/` = code and contracts shared by every agent: `portfolio_agent.core` (geometry, assets, guardrails, page metrics), `contracts/` (JSON schemas), `checks/` (stdlib checkers), `ARCHITECTURE.md` (layer rules). Later: an HTTP wrapper (run/edit/review over the agents' CLIs) and a job store. No agent-specific logic here.
