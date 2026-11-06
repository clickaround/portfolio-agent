"""Interfaces between layers. Nothing here imports another layer; implementations live in `authors/*` and `backends/*`.

Dependency rule (enforced by tests/test_architecture.py):
    core  <-  authors/*, backends/*  <-  engine  <-  cli
A backend or an author never imports `engine`; `core` imports no other layer.

Data that crosses layers is plain JSON-able dicts that follow `contracts/*.schema.json`:
    manifest  (asset-manifest)   : immutable source assets + sha256
    brief     : {title, domain, audience, keywords, sections}
    plan      : {pages:[{page, role, assets, title, text, caption, ...}], hero_min_ratio, ...}   (author-defined extras allowed)
    scene     : SceneDocument, mm coordinates, one per page (contracts/scene-document.schema.json)
    spec      : output spec (formats/output-contract.schema.json) + `style` token dict
"""
from typing import Protocol, runtime_checkable, Iterable, Any

Scene = dict
Manifest = dict
Plan = dict
Spec = dict


@runtime_checkable
class TextMeasurer(Protocol):
    """Answers 'does this text fit this box?' for the SAME engine that will render the final output."""

    name: str

    def configure(self, style: dict) -> None: ...

    def text_fits(self, text: str, w_mm: float, h_mm: float, size_pt: float, bold: bool = False, style: dict | None = None) -> bool: ...

    def font_available(self, name: str) -> bool:
        """True if `name` (font file stem or path) can be rendered by this backend. Authors use it to choose a display family."""
        ...


@runtime_checkable
class Exporter(Protocol):
    """Turns scenes into files. `formats` is a subset of capabilities, e.g. {'pdf','pptx','native','idml'}."""

    name: str
    capabilities: frozenset

    def export(self, scenes: Iterable[Scene], manifest: Manifest, project_root: str, out_base: str, spec: Spec, formats: Iterable[str]) -> dict:
        """Returns {'files': {fmt: path|None}, 'exit': int, 'notes': [...]} and never mutates source assets."""
        ...


@runtime_checkable
class Author(Protocol):
    """Produces a plan + scenes. Rule-based, host-agent-authored, or any future generator."""

    name: str
    can_relayout: bool

    def propose(self, brief: dict, manifest: Manifest, spec: Spec, measurer: TextMeasurer, options: dict) -> tuple[Plan, list[Scene]]: ...

    def relayout(self, page_plan: dict, scene_before: Scene, manifest: Manifest, spec: Spec, weight_mult: dict) -> Scene:
        """Only meaningful when can_relayout is True; must keep element ids, text and asset ids unchanged."""
        ...


class Issue(dict):
    """Gate/QA finding: {'code', 'elements', 'details', 'page'?}. Codes are stable strings, see core/gates.py."""
