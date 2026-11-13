# sourcePrepAgent Guardrails

<!-- Harness² C2 guardrails (guardrails.md). Every call. Hard constraints that hold regardless of task or tool. -->

1. Source bytes are never modified. The original is kept in `sources/`.
2. Every transform is explicit, recorded in `derived.json` with engine, hashes and parameters, and reversible.
3. No derivative is written without `--approve`; without it only the proposal and its sheet exist.
4. Cut-outs run only on files the host named with `--files`.
5. High-risk crops and any generative reconstruction need the user's approval.
6. Import `portfolio_agent.core` only; never import portfolioAgent or reviewAgent code.
7. No deploy, purchase, secret access or mass scraping without the owner's permission.
