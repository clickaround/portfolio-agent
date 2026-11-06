> **ARCHIVED V2; historical validation only.** Current v3 authoritative docs: GOALS.md, PLANS.md, architecture/ARCHITECTURE_MAP.md, formats/, research/repos.lock.json.

# Interface contracts (proposed / freeze at P05 only)

## Pipeline
`SourceManifest → SourceEvidence → ProjectBrief → BookPlan → LayoutCandidates → DesignArtifact → QualityReport → TargetedPatch → ExportBundle`.

## Every interface
- `schema_version`, `run_id`, `source_ids`, `created_at`, `producer`, `input_hash`, `warnings`.
- No raw screenshot pretending to be editable. A backend must declare supported native object types and fidelity limits.
- `Result = {ok, artifact_uri, warnings, error:{code, retryable, evidence_path}}` (proposed).

## Native editor interface (target behavior)
```
capabilities() -> {formats, layer_types, native_pdf, vector_export, headless}
create(book_plan, source_manifest, design_profile) -> editable_document_id
inspect(document_id) -> objects_by_stable_id, page_specs
apply_patch(document_id, operations[], expected_revision) -> {revision,diff}
render(document_id, page_range) -> previews[]
export(document_id, 'pdf' | 'editable') -> artifact + report
```

IDs are stable across edits. `expected_revision` prevents lost updates. Source references are immutable IDs, not arbitrary free-form file paths. A user's 'scale drawing 20%' must not silently crop or regenerate the plan. If backend cannot comply, expose the limitation, do not fake success.

## Source evidence
Each asset keeps immutable filename/hash, access rights, role, source page/region, original dimensions, allowed transformations, whether crop is explicitly approved, and factual claim links.

## Repair patch
`{target_id, op, value, anchor, allowed_reflow_ids, reason, previous_revision}`. Unknown targets and unsupported operations fail closed. Track `before` and `after` document hashes, including unchanged pages.

## Versioning
Change schemas only via migration/tests; never silently mutate customer source or prior output. Schema v0.1.0 shipped here is a proposal; `contracts/scene-document.schema.json` is intentionally a thin JSON demo, not a complete editor representation.
