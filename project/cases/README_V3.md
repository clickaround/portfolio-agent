# Reference cases are REQUIRED for final quality validation

A reference is a **complete portfolio/sequence**, not only an attractive screenshot. For each case record purpose, target audience, disciplinary domain, creator/credit, full project sequence, page role and dominant asset, hierarchy/whitespace/type/ratio, evidence of positive quality, limitations, source provenance, permission scope, and layout extraction confidence.

Three separate sets:
1. `cases/catalog.link-only.jsonl`: candidate URLs and metadata, **not local scraped content or legally cleared images**.
2. `cases/approved/`: licensed/consented files + rights documents (gitignored when private).
3. `cases/heldout/`: independent evaluation cases and separate creator/project split (no leakage into retrieval).

A public URL or 'found online' is never consent to store, train, redistribute, sell or copy. Use human-approved exemplars to derive general *editorial principles*, not recreate design identity. A small synthetic fixture is allowed for technical plumbing, never to claim professional quality.

Collection pipeline: discover (metadata only) → candidate scoring → rights check → source retrieval → whole-sequence inspection → human annotation → agreement check → searchable manifest → holdout split → 2–3 item retrieval → originality/rights guard before generation.
