# OpenPencil independent probe (T206) - 2026-11-04, Windows 11, Node (no bun), REPRODUCED for the listed commands only
- Install: `npm install @open-pencil/cli --ignore-scripts --prefix .cache/bin/openpencil` -> @open-pencil/cli 0.16.0 (MIT), 142 packages, no install scripts run. Repo clone pinned separately (.cache/vendor/openpencil, 0.17.0-beta.1) was NOT built/run.
- Windows bug in 0.16.0: CanvasKit wasm path became `C:\C:\...` (`new URL(..).pathname`). Local patch (fileURLToPath) applied ONLY to our .cache copy (originals kept as *.orig). Not upstreamed.
- `openpencil import page.html -o p.fig` works headless: 1 page, FRAME/TEXT nodes, positions preserved (mm->px converted by us).
- `<img src="file:///...">` -> EMPTY frames (source image lost = G1/G2 fidelity failure). With base64 data URI -> images render at the right place/aspect.
- `export -f png`: text NOT visible (fonts: "Inter, Malgun Gothic" not available to headless raster); images visible.
- `export -f svg`: text only in our sample (images not emitted as <image>); `export -f pptx`: 2 editable text shapes (images not verified); `export -f pdf`: FAILS ("Cannot read properties of undefined (reading 'jsPDF')").
- PDF assets (vector drawings) cannot go through HTML import at all -> vector preservation NOT possible via this path.
Verdict for our product: not usable as the PDF/print path in this setup; possible only as an editable .fig/PPTX exporter after (a) data-URI images, (b) font bundling, (c) PDF bug fix. Alternative remains DesignCraft (PDF/IDML/PPTX/native all OK in spike).
Not tested: MCP server, GUI editor, .pen format, local-edit via `eval`/tool calls, newer 0.17 beta (PDF bug may be fixed there).
