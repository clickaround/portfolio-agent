---
name: portfolio-review
description: Critique a rendered portfolio for source-fact fidelity, domain fit, editorial hierarchy, page rhythm, structural defects, editability, and unintended changes before submission.
---
# Portfolio Review (bounded critique)

Given rendered pages AND source documents, read `benchmarks/SPEC.md`, `benchmarks/HUMAN_REVIEW.md`, relevant domain guidance. Do deterministic checks FIRST (using `scripts/check_layout.py` only for its limited JSON-box scope), then source evidence and domain-aware visual composition. Separate HARD FAIL from subjective preference. Inspect at actual zoom/print size for architectural linework. Report exact page/element defect, severity, evidence, and **minimal local patch**; don't rewrite entire document or secretly add artwork. Do not claim visual verification unless you inspected real rendered pages. Output a review report and ask for revised render; max iterations set in active plan.
