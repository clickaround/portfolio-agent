from pathlib import Path

from ..gateways import agents


def read_brief(d: Path) -> str:
    return (d / "project.md").read_text(encoding="utf-8")


def write_brief(d: Path, markdown: str) -> int:
    (d / "project.md").write_text(markdown, encoding="utf-8")
    return len(markdown.encode("utf-8"))


def manifest(d: Path) -> dict:
    """Assets (ids, roles, aspects, source_transform / cutout flags) and the parsed brief, exactly what the agents see."""
    m, brief = agents.ingest(d)
    return {"manifest": m, "brief": brief}
