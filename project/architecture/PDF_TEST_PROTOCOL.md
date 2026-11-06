# PDF/vector fidelity spike specification

1. Generate a **synthetic** PDF containing visible vector lines of multiple weights, embedded font text, small dimension labels, dashed geometry, hatches or equivalent patterns, crop marks and a raster image. No copyrighted architectural sheet needed for first test.
2. Record SHA-256 of original bytes, PDF object/page counts, fonts, raster/vector operator information where available, and visual baseline at 150/300 DPI.
3. Put that source into an A3 landscape layout with allowed uniform scale only; disallow any crop/AI redraw unless separately approved.
4. Export to PDF, re-open in a **different renderer**, inspect at 100/400% zoom and raster comparison with correct geometry alignment; manually inspect text, dimension arrowheads, weights and text extraction.
5. Accept only after source immutable, no missing semantic labels, no unapproved crop, no unsupported font substitution, and backed-by-evidence editability claim. Do not equate same source SHA with faithful placed output.
6. If native backend rasterizes drawing, label it explicit `raster_only` and fail a `vector_required` gate. Investigate original vector PDF embedding as a separate export path.
7. Capture environment, renderer versions, exact commands, artifacts, comparison screenshots and reviewer notes; treat zero-byte or corrupt output as FAIL.

**Limitations:** image SSIM/PSNR do not prove vector editability or semantic preservation; bounding-box tests cannot detect thin line loss; verifying one synthetic PDF doesn't prove real CAD/BIM PDF support.
