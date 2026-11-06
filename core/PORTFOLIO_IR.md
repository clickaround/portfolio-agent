# Portfolio IR (proposed, not implemented)

Inputs: ordered project IDs, asset manifest with immutable hashes and source-provenance, project claims with citations/confidence, audience and domain pack, lawful case references, output format spec. 

Intermediate: `BookPlan` (sequence, narrative, page roles, hero/support, exclusions), `SceneDocument` (typed visual layers, millimeter coordinates, z-order, crop transforms, locks, owner asset ID), `DocumentRevision` (targeted operations and expected diff), `ExportArtifact` (format, rendering engine, version hash, evidence/QA).

`SceneDocument` is an open canonical contract candidate; do NOT let one vendor's internal object model become the common schema until explicit ADR. Domain fields belong to extensions rather than core. For screen/digital output, convert mm via stated dpi and record actual pixel sizes. Print/DTP must preserve margin, bleed, trim, binding and facing pages.
