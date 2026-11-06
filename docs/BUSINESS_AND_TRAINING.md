# Training decision and commercialization — after measurable trials

## When to train (not now)
1. Is there a consistent *candidate generation* problem? All candidates fail editorial criteria across diverse projects even with good references. Consider design grammar/layout generation study.
2. Is it a *selection* problem? A good candidate is present but model ranking chooses worse repeatedly; collect independent expert **preference pairs** with creator-disjoint splits before training a ranker.
3. Is it a source/analysis problem? Wrong plan/section labels or invented roles; improve extraction/provenance or domain labels before fine-tuning.
4. Is it a deterministic editing error? Train nothing; fix exporter/geometry/contract.

Training path only if rights explicitly permit it: reference-only permission ≠ training permission. Store provenance and withdrawal mechanism. Measure heldout delta vs no-training baselines and total labeled-data/labor/GPU cost.

## Business go/no-go
- First customer: architect/student with real portfolio, via plugin; record installation friction and time saved. Check target employer/school policy on AI assistance.
- Pilot measure: quality people would actually submit, edits required, paid intent, throughput, cost per 2-page job, confidentiality expectations.
- Avoid generic 'AI portfolio generator' value prop. Focus on **editable, source-faithful editorial storytelling**.
- Plugin may be too technical for many designers: if paid demand emerges, add hosted service only after evidence.
- HarnessRouter Starter Kit's commercial license is not automatically covered by CE Apache-2.0; get approval before code reuse.

No forecasts, market size or pricing data are asserted by this design document. P08 asks for explicit paid experiments, not assumed revenue.
