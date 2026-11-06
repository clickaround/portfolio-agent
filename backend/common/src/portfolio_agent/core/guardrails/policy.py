"""Guardrail POLICY: which codes block and which only advise, type-size floors. One place to read, one place to change (ADR-0009)."""

# G1-G5 of benchmarks/SPEC.md are BLOCKING; composition diagnostics (score L) are ADVISORY: reported, never silently dropped,
# never a reason to refuse export (research/PAPER_NOTES_AUTODESIGN_HARNESS.md: blocking vs non-blocking checks).
BLOCKING = frozenset({"BBOX_OVERLAP", "OUTSIDE_MARGIN", "ASPECT_DISTORTION", "TEXT_OVERFLOW", "MISSING_ASSET_ON_PAGE", "SOURCE_MODIFIED", "UNKNOWN_ASSET",
                      "LOCKED_TARGET_EDITED", "TYPE_TOO_SMALL", "TEXT_OVER_IMAGE", "PDF_PAGE_COUNT", "PDF_PAGE_SIZE", "PDF_TEXT_NOT_EXTRACTABLE", "PDF_VECTOR_LOST", "PDF_IMAGE_MISSING"})
ADVISORY = frozenset({"REPEATED_LAYOUT", "HERO_TOO_SMALL", "TEXT_UNGROUNDED", "WHITESPACE_EXCESS", "IMBALANCE", "DRAWING_SMALL"})
DRAWING_MIN_FRAC = 0.12   # a drawing below 12 % of the content area reads as a thumbnail (blind11-13: "cut down to thumbnails"); index pages are exempt
MIN_PT = {"body": 8.0, "small": 6.5}   # print floors (Butterick 10-12 pt body; labels/folios may go to 6.5)


def split(issues):
    """-> (blocking, advisory). Unknown codes count as blocking (fail closed)."""
    return [i for i in issues if i["code"] not in ADVISORY], [i for i in issues if i["code"] in ADVISORY]
