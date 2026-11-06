# Output format contract

A **Portfolio** has a medium (`print`, `presentation`, `digital`), trim dimensions (mm), media-specific export profiles, optional facing-page/spread flag, desired number of pages, reading direction, binding, margins, gutters, bleed, safe area, and font/embed policy. A **Page** inherits it or overrides intentionally. Every element has content-aware crop rules and normalized/physical geometry. Never use A3 as a hidden default.

- Print: trim/bleed/crop marks when supported, raster effective PPI, CMYK/PDF-X only after the selected backend proves it, vector-source preservation.
- Screen: logical px + scale factor, responsive viewport policy, visual safe area.
- Presentation: slide dimensions and native element editability.
- Custom: validated finite positive dimensions and max limits. Facing spreads must not confuse page count with spread count.
- Cross-format reflow generates a new version; preserve old source state and record meaningful crop/text decisions.
