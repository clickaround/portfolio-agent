# Backend decision matrix — NOT FROZEN

| Role | Lead candidate | Alternative | Mandatory spike | Failure/fallback |
|---|---|---|---|---|
| Multi-page editorial DTP | DesignCraft (pre-alpha) | Vivliostyle/Paged.js | arbitrary mm trim, facing-page master, bleed, text wrap, PDF fonts/vectors | HTML/CSS/SVG printed PDF |
| Freely editable image+text canvas | OpenPencil | FigCraft, Penpot, Fabric | layer CRUD, local edits, export parity, offline | simple authored HTML source |
| Office/PPTX decks | GenOffice | DeckCraft, html-to-editable-pptx | native object editability and re-export | HTML deck + PDF (PPTX deferred) |
| Raster asset retouch | PhotoCraft | image tools installed locally | image format support, mask and preservation | original supplied asset |
| Vector asset retouch | VectorCraft | Graphite | SVG import/export, editable path, fonts | original SVG |
| Diagrams | Diagram Design | custom SVG | geometry self_check, fixed source claims | omit optional diagram |
| Harness routing | direct Claude/Codex | HarnessRouter CE | plugin/skills/files/session recovery and cost | direct hosts remain supported |

**No backend is integrated or approved until a pinned reproduction with source-fidelity, editability and renderer comparison exists.**

Prioritize DTP vs free-canvas by medium, not a forced universal editor. Read the `storytold/` family separately—brand artwork isn't necessarily redistributable. Read kit-specific license terms before using starter kit code in any commercial prototype.
