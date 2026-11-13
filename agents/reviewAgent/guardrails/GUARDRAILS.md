# reviewAgent Guardrails

<!-- Harness² C2 guardrails (guardrails.md). Every call. Hard constraints that hold regardless of task or tool. -->

1. A review is valid only if its hashes match the current `review-context.json`. A stale or unbound review is rejected.
2. The reviewer is fresh: it did not plan, lay out or repair the attempt it reviews.
3. `finalize` requires passing blocking gates and a passing fresh review. Neither alone is enough.
4. One LLM critic's number is noise (about +-0.07). Never claim quality from it; human blind pairwise review is the evidence.
5. The unblind key, rubric answers and earlier verdicts are never given to a generating agent or written into any agent's memory.
6. Content fidelity, spatial correctness and design quality are reported separately, never as one mixed number.
7. Import `portfolio_agent.core` only; never import portfolioAgent or sourcePrepAgent code.
8. No deploy, purchase, secret access or mass scraping without the owner's permission.
