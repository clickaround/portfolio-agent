# Paper review and evidence contracts

Review priority: GraphicDesignBench (GDB), SlidesGen-Bench (incl. PEI), DECKBench (multi-turn), AutoDesign/PosterBench, DeepSlides, Paper2Poster. For each research note record:
- Paper identity: title, authors, DOI/arXiv, version/date, source link.
- Task and assumptions, architecture diagram, precise intermediate representation.
- Whether output is raster/vector/editable native; page/deck level.
- Data sources, label quality, rights, split/leakage.
- Measured metrics, human alignment and negative results; all numbers with table/figure reference.
- Official code: link to precise source file, entrypoint, SHA, dependencies and reproduction command.
- What our product can inherit, what cannot transfer to multiple disciplines, and cheapest falsification test.

**No claim 'paper reproduced' until executed.** Benchmark code must be tested independently of generation to prevent evaluator leakage. Human ranking is independent of model judge prompts.
