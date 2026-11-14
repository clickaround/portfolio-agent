---
name: portfolio-edit
description: Apply localized edits to portfolio page assets while preserving unrelated objects.
---
# Portfolio Edit

Read input Scene/document version and user instruction, identify exact target element IDs, freeze all other objects, calculate proposed operation and affected constraints; compare before/after documents by ID and source hashes. Never overwrite original artwork/CAD/screenshot/source PDF. If resize/reflow modifies other elements, show an explicit diff, flag as relocation rather than local edit, and request permission for fidelity-affecting edits. Rerender changed page and verify export. Report changed objects, unchanged object count, errors and provenance.

## Runtime (implemented)
`python scripts/portfolio.py edit <out_dir> <page-XX> <element-id> "<new text>"` edits one unlocked text element, re-exports, and only commits if scene diff is limited to the target, QA passes and zero pixels outside the target box (and other pages) changed. Locked (source-asset) elements are refused. An accepted edit is recorded as the next attempt (`attempts/NN`, with fresh previews); run `review-context` again before any review, because the earlier review was bound to the previous attempt.
