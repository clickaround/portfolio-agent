# Baselines and ablation controls

Same project assets, output dimensions A3, page count two, purpose, objective, output verification script and user task. Keep model/provider settings as equivalent as available. Run 2+ trials where budget permits, report variance and failure rate.

| ID | Model/host | Cases | Domain guidance | Backend | QA | Objective |
|---|---|---|---|---|---|---|
| B0 | same Claude/Codex separately | none | none | direct HTML | no | original coding-agent capability |
| B1 | same | none | yes | direct HTML | no | knowledge pack contribution |
| B2 | same | authorized 2–3 | yes | chosen verified backend | hard-gate only | cases + editability contribution |
| B3 | same | same | yes | same | hard gates + limited visual repair | critic contribution vs cost |

**Avoid confounds:** changing backend between B1/B2 mixes retrieval with rendering; optionally add B1b `same backend, no cases` to isolate case effect. Compare quality per cost budget in addition to free-budget quality. Host/model is an experiment dimension, not a random setting.

Report: pass counts by gate, independent aesthetic preference wins/ties, content QA %, local patch unintended diff count, cost USD, runtime sec, human editing minutes. No universal single-score winner.
