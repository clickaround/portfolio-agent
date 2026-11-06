# Layout craft — how designers actually set a page (cited rules, DOC_REPORTED 2026-11-04)

These are the rules `authors/rule_based` implements. Each has a source; "opinion" marks practitioner recommendations rather than standards. Numbers in mm/pt are what the code uses.

## 1. Page anatomy (vocabulary used in code)
margins = live area between format edge and content; columns = vertical alignments that create starting/stopping points for text AND image; gutter = blank column between columns; flowlines = horizontal bands that impose starting/stopping points (a *hang line* is the flowline images and text hang from); modules = column x flowline units; marker = fixed position for subordinate recurring text (folios, section titles).
Source: University of Washington IMAGE 211 "Grids" handout, pp.4-10 (courses.washington.edu/image211/handouts/Grids.pdf). "An effective grid is not a rigid formula, but a flexible and resilient structure" (p.90).

## 2. Margins
- Classical canon (Van de Graaf / Rosarivo / Tschichold): type area = page minus 1/9 top+inner and 2/9 bottom+outer; margins inner:top:outer:bottom = 2:3:4:6 on a 2:3 page -> type area about 4/9 of the page. Books, not portfolios; we keep the *principle*: bottom margin > top margin, generous outer space. (en.wikipedia.org/wiki/Canons_of_page_construction)
- Portfolio practice (opinion): outer margin 15-20 mm on A3, gutters 4-6 mm, bleed 3 mm, 12-column grid for flexibility, 6 for image-heavy pages. (illustrarch.com, "architecture portfolio layout grid")
- Code: margins from the output spec (user-set); default 12 mm A4 / scaled; **bottom band = footer marker**, **top band = running-header marker** so content hangs from one flowline below the header.

## 3. Grid use
- Images and text share the same left/right edges by snapping to columns; a hero may run all 12 columns; a drawing beside a short text sits in a 4-8 split; keep ONE grid system for the whole document. (illustrarch, opinion; consistent with UW handout)
- Keep caption position identical from page to page; build 2-3 reusable page templates and keep title placement, caption position and image alignment fixed. (illustrarch)
- "Keep one layout aspect consistent throughout, and direct the viewer's eye to your strongest work"; lead each project with the strongest image. (Georgia Tech SoA portfolio guidelines; illustrarch)

## 4. Type
- Body text in print: **10-12 pt** (Butterick, Practical Typography, "point size"); portfolio practice 9-10 pt (illustrarch, opinion). Code default 10 pt body, user-overridable.
- Line spacing: **120-145 % of point size** (Butterick, "line spacing"). Code: body 1.35, captions 1.3, display 1.05-1.1.
- Line length: **45-90 characters incl. spaces** (Butterick) / 45-75, ~66 ideal, 40-50 in multi-column (Bringhurst, Elements of Typographic Style, via clagnut.com & caretypography.com). Code: text columns are sized to 45-70 characters at body size; a wider column is narrowed, never stretched.
- Hierarchy: modular scale ratio 1.25 (major third) or 1.333 (perfect fourth); display may use a larger ratio. Captions one step smaller than body. (figr.design/typography-scale, illustrarch; opinion-grade) Code: label 0.8x body, caption 0.9x, heading 1.6x-2.0x, display 3.2x-3.6x.
- One or two type families (illustrarch, opinion). Code: display family (serif if installed and text is Latin) + body family; never a third.

## 5. White space and pacing
- Treat white space as a material; protect generous empty areas (illustrarch). Alternate pacing: hero spread then drawing/process spread (knowledge/domains/architecture.md). Repeated 3-column cards = report-style failure (same).
- Code: empty space must be *bounded by the grid* (a text column left deliberately short, a hero hanging from the hang line) rather than leftover after a fit.

## 6. Recurring furniture
- Markers: running header (project title left, "NN / total  SECTION" right), folio in the footer band, section label above headings. Page numbers may be large but light (tutsplus, opinion). All switchable by the user (`style.header`, `style.footer`).

## Not found / not claimed
No standard specifies a hero-image area ratio; `hero_min_ratio` in patterns stays our own heuristic. UIC and UT-Austin portfolio guides could not be fetched (login / Issuu shell). None of these sources validates *our* output quality; only blind review does.
