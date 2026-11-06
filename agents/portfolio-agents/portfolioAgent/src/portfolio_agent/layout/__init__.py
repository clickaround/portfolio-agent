"""layout: deterministic page composition primitives (grid, type system, compositions, guillotine solver).
No editorial decisions live here: callers (authors) decide roles, asset order and words; this layer turns a page plan into a SceneDocument.
Imports only `core`. Rules and sources: knowledge/editorial/layout-craft.md.
"""
from .book import build_book, build_scene, pick  # noqa: F401
