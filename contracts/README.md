# Interface contracts — **draft**

- All structured model outputs must be validated; a schema-valid payload can still be semantically wrong.
- `asset-manifest.schema.json` describes immutable source files. Real runs calculate SHA256 from bytes.
- `book-plan.schema.json` says *why and what*; claims must reference manifest asset IDs.
- `scene-document.schema.json` records *where*, with page size/element boxes in millimeters. An editable backend may also store a native file; Scene is the auditable intermediate and expected semantics, not automatically lossless roundtrip format.
- `design-profile.schema.json` records typography/grid/color rules.
- `evaluation-report.schema.json` separates hard gates from aesthetic scores.

This package validates JSON syntax with stdlib `scripts/validate_package.py`. A production implementation must add a proper JSON Schema validator and cross-file referential integrity checks. Do not mistake the sample box validator for full PDF fidelity/typography QA.
