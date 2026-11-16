# T1009 evidence — PosterCopilot as a layout proposer, as it is (REPRODUCED; verdict: not usable without training on our pages)

Date 2026-11-15. Windows 11, RTX 5080 Laptop 16 GB VRAM.

- Weights: `void-2024/PosterCopilot` (Apache-2.0, 16.6 GB, four safetensors shards), saved outside the repo in
  `C:/DK/real_sources/models/PosterCopilot`.
- Reference code: https://github.com/JiazheWei/PosterCopilot at `aa1de672034facb9e2b7b472ab6ea56234a5b80c`, cloned into the ignored
  `.cache/vendor/PosterCopilot`. README says Apache 2.0; the repo has no LICENSE file. Read before running: `infer.py`, `postercopilot/*.py`
  (no network, no subprocess, no eval). Not copied into our code.
- Environment: separate venv `.cache/venvs/pc`, Python 3.11.7, torch 2.8.0+cu128 (2.11.0 failed to import: WinError 1114 on `c10.dll`),
  transformers 4.57.3, bitsandbytes 0.50.2, qwen-vl-utils 0.0.14.
- Scripts: `project/research/p10_postercopilot/pc_prep.py` (our pages -> layer folders), `pc_run.py` (same preprocessing, prompt and
  greedy decoding as the reference predictor, 8-bit load).
- Load: 8-bit, 34 s, 8.8 GiB VRAM. Five layouts took about 25 minutes in total on this laptop (not timed per job).

Check that the quantised load still behaves like the release (reference `examples/*/layout.json` vs ours, px differences x, y, w, h):
- jazz-day (800 x 1600): three of five layers identical or within 3 px; one text layer +10, -2, +20, +24; one picture 115 px lower.
- klean-energy (1753 x 2480): within 41 px on position, one layer 82 x 80 px larger.
So 8-bit gives the same kind of layout as the published result, not the same numbers.

Our pages (arch_01, A4 landscape 297 x 210 mm, pages 01, 02, 04; running header and hairlines left out; each element cropped from the
rendered page as a layer): `evidence/P10-postercopilot-compare.png` (sha256 2f76cacb60e20454…), rule layout left, model right.
- page-01: picture stretched to the full page (297 x 210) as a background, titles shrunk to 9 mm high strips at the bottom, caption blown up.
- page-02: picture squeezed into the top third (297 x 71, source aspect 2.5 kept only roughly), the 4 mm label stretched to 277 x 60 mm,
  title shrunk to 6 mm.
- page-04: one picture enlarged to the left edge and top (bleed), the other kept; captions separated from their pictures.
- Gates were not run: every page already fails by eye (text scaled out of its aspect ratio, type sizes ignored, captions detached).

Limits of this test
- My text layers were opaque white crops, not transparent text layers as in the training data; that makes text look worse than it would.
- One book, three pages; the card asked for three books. The failure is of kind, not of degree, so more books were not run.

Reading: the model composes a poster (one hero picture behind, text on top, free scaling). A portfolio page needs fixed type sizes, pictures
at their own aspect ratio, margins and captions tied to pictures. As it is, it is not a proposer for us. It remains a candidate base to
fine-tune (T1013) once portfolio layout records exist (T1011); 8-bit inference fits this machine, training a 7B model on 16 GB does not look
realistic here (HYPOTHESIS, not tried).
