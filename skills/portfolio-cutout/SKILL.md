---
name: portfolio-cutout
description: Remove the background of chosen photographs (products, models, objects, people) so they sit on the book's paper - the host decides WHICH, the engine cuts. Use when a project's photos show a subject on a background that adds nothing (studio shots, model photos on a desk, product renders on grey), or when the user asks for 누끼 / cut-outs.
---

# Cut-outs (누끼)

You decide, the engine executes. Never cut out blindly: a photograph of a building in its street, a drawing, a scan, a diagram, an interior - their context IS the content. Cut out only when the subject is the content and the background is noise: a physical model on a table, a product on a sweep, a person for a profile page, an object for a detail row.

1. Look at `preview`/`manifest` (or the files in `images/`), choose the files, and run
   `python scripts/portfolio.py cutout <project> --files model_01.jpg,product_02.png --sheet <out>/cutout_sheet.png`
   (engine: `rembg` = danielgatis/rembg, MIT, u2net ONNX, local CPU, offline once the model is cached; `--engine photocraft` = storytold/photocraft Select Subject, Apache-2.0, BLOCKED until its signed Windows binary is verified).
2. Look at `cutout_sheet.png` (before / after on a checkerboard). Reject a cut-out that lost part of the subject (thin legs, glass, hair) - restore by deleting the png and copying the original back from `sources/`.
3. The result is `images/<stem>.png` (RGBA, trimmed to the subject + 4 % air); the original stays byte-identical in `sources/` and `derived.json` records `transform: cutout`, engine, hashes and the alpha bbox; the manifest shows it as `source_transform` and `cutout: true`.
4. Place cut-outs on white (`split`, `hero`, `pair`, `grid`); never on a `bleed` page and never on a `dark` page unless the subject is light. Captions still name what the photo shows and where the background went ("Model photograph, background removed").

Rules: transforms are explicit and reversible (AGENTS.md); the subject's pixels are never repainted or generated - a cut-out only masks. A generative "reconstruction" of a missing edge needs the user's approval and is not what this skill does.
