# Rights-safe Portfolio Case Library

**Case examples are required to develop domain taste; mass scraping and model training are NOT initially required.**

## Rights are purpose-specific
`view_link`, `download/store`, `derive_annotations`, `retrieve_as_reference`, `use_for_eval`, `train_model`, `redistribute_output` are distinct scopes. No scope is implied by a public page.

A candidate URL may be kept as metadata under `link_only`; its images/PDFs are not copied into the ZIP. Permission evidence stores who granted what, when, allowed uses, and withdrawal contact. On withdrawal, remove stored copies, cached derivatives and search index entries; review experiment use and audit logs.

## Full portfolio annotation (not just one appealing page)
For each authorized whole portfolio: `case_id, author/creator_id, purpose, intended reader, project_count, page_count, sequence rationale`. Each page/spread: `role, project_id, dominant asset, supporting assets, relative area, whitespace/density, grid alignment, type hierarchy, narrative transition, interpretation vs observation, why this is professionally useful`. Flag unknowns.

## Quality and permissions must not be conflated
`quality_verified: false` until independent expert review. `rights_status: link_only` never qualifies as licensed reference retrieval. Rights restrictions may differ for human review, embedding retrieval, external model calls and training. User-uploaded assets are used to perform the requested task only, not to train without express opt-in.

## Acceptance hierarchy
- Synthetic author-created fixtures: technical pipeline testing only.
- User-owned and explicitly submitted sources: may generate user's specific portfolio subject to rights scope.
- Permission-approved external cases: references for controlled retrieval and human quality analysis.
- Heldout approved cases: evaluation only, never retrieval or prompt examples.

## Acquisition failure behavior
If 0 approved external cases exist, run domain-guideline + synthetic source workflow and tag outputs `NO_EXTERNAL_REFERENCE`. Continue backend work. Do NOT state professional quality or allow unauthorized case retrieval. Actual human taste benchmark is BLOCKED until suitable independent portfolios/reviewers exist.
