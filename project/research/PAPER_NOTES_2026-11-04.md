# Paper notes (read 2026-11-04 via arXiv abstract + HTML; evidence label DOC_REPORTED, none reproduced by us)

HTML fetches were truncated (SlidesGen-Bench and GDB: first ~100k of ~190k/220k chars read; appendices, Discussion, SVG/animation results NOT read). Numbers below are quoted from what was read.

## SlidesGen-Bench — arXiv 2601.09487 (v2 2026-08-21, EMNLP 2026 Main)
- Task: compare heterogeneous slide generators by projecting outputs to renderings; three axes: content, aesthetics, editability.
- Content: QuizBank. 10 MCQs/document (5 concept, 5 data), written from the source PDF by a forensic-analyst + critic loop; a VLM converts slide images to Markdown, then answers using only that text; accuracy = content score (1.2% of errors from extraction failures).
- Aesthetics (computational): Harmony = fit to hue templates in HSV (Cohen-Or 2006), deck = mean minus cross-slide std penalty; Engagement = colorfulness (Hasler & Süsstrunk 2003) with a deck pacing term; Usability = figure-ground contrast in text regions, mapped ln(c)/ln(21); Visual Rhythm = subband-entropy clutter (Rosenholtz 2007) + RMSSD across slides (needs >= 5 slides). Overall = sum.
- Editability PEI (knockout levels): L0 Static image, L1 Patchwork (text editable), L2 Vector, L3 Structural (masters, grouping), L4 Parametric (native charts), L5 Cinematic (animation).
- Human alignment (Slides-Align1.5k, 9 systems x 7 scenarios), Spearman avg: SlidesGen-Bench 0.71, LLM-judge rating 0.57, LLM-judge arena 0.52, PPTAgent 0.53, humans 0.85.
- Stated limits: static only; QuizBank depends on the VLM; PEI is format-conditional (image/web outputs face a ceiling); metrics assume visual-ergonomics and may need recalibration outside the validated distribution; data mainly English, corporate/academic. Larger rank errors on image-rich/creative decks.
- For us: reuse the computational aesthetics only as DIAGNOSTIC scores (never gates, as SPEC.md already says); PEI is a usable editability scale for E; its distribution (slides) is not portfolios.

## GraphicDesignBench (GDB) — arXiv 2604.04192 (v2 2026-04-07)
- 49-50 tasks, 5 axes (layout, typography, infographics, template/semantics, animation), understanding + generation, on LICA layered designs. Layout tasks use 989 non-video layouts; typography 2,568 text elements; generation sets ~100 samples (multi-aspect adaptation 13 layouts).
- Results quoted: partial-completion multi-element mIoU Gemini-3.1-Pro 0.2007, GPT-5.4 0.1620, Claude-Opus-4.6 0.1286; font-family accuracy GPT-5.4 0.237, Claude-Opus-4.6 0.006; font-size MAE GPT-5.4 8.97 px, Claude 10.84 px; style-range exact match 0.000 for all models.
- Conclusion: frontier models are weak at precise spatial reasoning, typographic perception and structure; high-level semantics is easier.
- Limits: small generation sets; not every model on every task; brand dependence and evolving trends not addressed.
- For us: supports NOT letting the LLM emit pixel coordinates (matches design: tokens/constraints, deterministic geometry) and keeping hard geometry gates deterministic.

## DECKBench — arXiv 2602.13318 (2026-02-10)
- Generation + multi-turn editing. Slide metrics: text sim (embedding), figure sim (CLIP-ViT-B/32), perplexity, faithfulness; deck metrics: DTW, transition similarity, deck fidelity/faithfulness, LLM judge (no results reported); multi-turn: DeltaDTW, DeltaTransSim vs a human-edited reference. Edit instructions come from a user-simulator with 3 personas (granular/balanced/executive).
- Reported: every baseline had elements beyond slide boundaries and poor figure scaling; Auto-Slides 7.8% failure rate; no correlation with human judgement is reported; "Layout" metric is undefined in the text; Table 5 caption (55 turns) conflicts with text (5 turns).
- For us: similarity-to-reference metrics do not measure novel design quality (SPEC.md already warns); the persona-based edit simulation idea fits AP-05..07.

## Paper2Poster — arXiv 2505.21497 (v2 2025-10-30, CC BY 4.0)
- PosterAgent: Parser -> Planner (binary-tree layout preserving reading order/spatial balance) -> Painter-Commenter (render code + VLM feedback to remove overflow). Metrics: visual quality, textual coherence, VLM-as-judge, PaperQuiz. Claims: Qwen-2.5 open variants beat GPT-4o multi-agent systems on nearly all metrics with 87% fewer tokens; 22-page paper -> editable pptx poster for about $0.005; reader engagement is the main aesthetic bottleneck. No dataset size on the abstract page.
- For us: tree layout adopted (re-implemented, MIT code); the painter-commenter loop = our repair + independent critic.

## Cross-cutting conclusions
1. No paper validates portfolio (multi-page, domain-specific, print) quality; all are slides/posters/templates. Our N, D axes need our own blinded human protocol.
2. Computational aesthetic scores correlate with humans only moderately (0.71 best) -> never a pass criterion.
3. Boundary/creative/minimal styles are where metrics fail most -> portfolios are exactly that regime.
Not read: paper appendices, SVG/animation sections of GDB, SlidesGen-Bench PEI appendix details, DECKBench appendices/persona prompts.
