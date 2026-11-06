# Repository code audit task

Choose a concrete `T20x` task from `tasks/backlog.json` and **exactly one** source repo from `research/repos.lock.json`. Pin its commit SHA and read the actual `README`, `LICENSE`, entrypoint, dependencies, skills, evaluation logic, dataset access and model/card where relevant. Distinguish author claims, inspected source and reproduced execution.

Record all preconditions (OS, Node/Python versions, keys, Docker size), one minimal isolated smoke command and known failure mode. Run only permitted commands; otherwise create a BLOCKED evidence packet. Never integrate a repo until its own example runs and the adapter contract is justified. Keep the actual code path and license distinct from author's screenshots.

Output to the task-specific evidence path in `tasks/cards/<id>.md`, with exact commands, exit codes, logs and counterevidence. Do not label paper benchmark scores as ours.
