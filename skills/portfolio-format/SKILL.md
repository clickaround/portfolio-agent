---
name: portfolio-format
description: Validate arbitrary page sizes, bleed, gutters, facing pages, raster and vector export needs.
---
# Portfolio Format

Read `formats/page-presets.json`, `formats/output-contract.schema.json`, `formats/README.md` and actual project OutputSpec. Dimensions are given in mm; for digital outputs include pixel dimensions and scale. Never assume A3/A4 or landscape. Validate positive finite width/height, bleed vs trim, binding/gutter, safe margin, and intended page/spread count. On resize choose reflow rather than uniform scaling when semantics, crop or readability would fail. Preserve source coordinates, vector data and provenance. Record print backend certification as unverified until explicitly measured.
