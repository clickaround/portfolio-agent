# Work decomposition & gate strategy

## DAG allocation
- P00: package/hosts/paths (integration lead).
- Parallel independent: reference discovery & rights (Case Curator), pinned repo metadata and safety review (Repo Auditor), medium/domain rubric (Domain Analyst).
- Serial handoff: ReferenceSelection → BookPlan → PageSpec → BackendRenderer → IndependentQA → ScopedRepair → Export.
- Parallel proposals: only independent layout candidates; one integration writer selects and commits final Scene. No concurrent writes to the final JSON.

## Agent count is not a quality metric
Run one-agent vs two-specialist ablation in P08 after product works. Capture elapsed time, model token cost, contradictory evidence counts, conflicts, and output blind preference. If multi-agent provides no measurable improvement, revert to one coordinator.

## Failure policy
Any missing rights/third-party runtime: document BLOCKED for that task and continue synthetic/fallback. Any source-fidelity failure: reject candidate regardless of aesthetics. At an approval gate do not mark the whole phase DONE based on partial tests. Avoid nested or recursive agent-to-agent delegation until deadlock and file-ownership tests pass.
