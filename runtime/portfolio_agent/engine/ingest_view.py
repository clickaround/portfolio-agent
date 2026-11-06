"""Read-only view of a project for host authors: asset ids/roles/aspects and the parsed brief."""
from portfolio_agent.core import assets


def view(project_dir):
    manifest, brief = assets.ingest(project_dir)
    slim = [{k: a[k] for k in ("id", "kind", "role", "width", "height", "aspect", "relative_path", "crop_allowed")} for a in manifest["assets"]]
    return {"project_id": manifest["project_id"], "assets": slim, "brief": brief}
