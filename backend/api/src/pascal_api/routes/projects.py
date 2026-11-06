from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import FileResponse

from .. import services
from ..models import BriefBody, ProjectCreate
from ..store import ASSET_KINDS

router = APIRouter(tags=["projects"])


@router.get("/projects")
def list_projects(request: Request):
    return request.app.state.store.list()


@router.post("/projects", status_code=201)
def create_project(body: ProjectCreate, request: Request):
    st = request.app.state.store
    st.create(body.id, body.title, body.brief)
    return st.meta(body.id)


@router.get("/projects/{pid}")
def get_project(pid: str, request: Request):
    return request.app.state.store.meta(pid)


@router.delete("/projects/{pid}", status_code=204)
def delete_project(pid: str, request: Request):
    request.app.state.store.delete(pid)


@router.get("/projects/{pid}/brief")
def get_brief(pid: str, request: Request):
    d = request.app.state.store.dir(pid)
    return {"markdown": (d / "project.md").read_text(encoding="utf-8")}


@router.put("/projects/{pid}/brief")
def put_brief(pid: str, body: BriefBody, request: Request):
    d = request.app.state.store.dir(pid)
    (d / "project.md").write_text(body.markdown, encoding="utf-8")
    return {"bytes": len(body.markdown.encode("utf-8"))}


@router.get("/projects/{pid}/manifest")
def get_manifest(pid: str, request: Request):
    """Assets (ids, roles, aspects, source_transform / cutout flags) and the parsed brief, exactly what the agents see."""
    return services.manifest(request.app.state.store.dir(pid))


@router.post("/projects/{pid}/assets/{kind}", status_code=201)
def upload_asset(pid: str, kind: str, request: Request, file: UploadFile = File(...)):
    """kind = images | drawings | diagrams. The file name becomes the asset id (stem)."""
    s = request.app.state
    p = s.store.add_asset(pid, kind, file.filename or "", file.file, s.settings.max_upload_mb * (1 << 20))
    return {"kind": kind, "file": p.name, "id": p.stem}


@router.delete("/projects/{pid}/assets/{kind}/{name}", status_code=204)
def delete_asset(pid: str, kind: str, name: str, request: Request):
    request.app.state.store.asset_path(pid, kind, name).unlink()


@router.get("/projects/{pid}/files/{kind}/{name}")
def get_file(pid: str, kind: str, name: str, request: Request):
    """Original or derived file (kind = images | drawings | diagrams | sources)."""
    return FileResponse(request.app.state.store.asset_path(pid, kind, name))


@router.get("/catalog")
def get_catalog():
    """Roles, page flags, grid systems, compositions, photo-set templates, exporter backends: what a book plan may use."""
    return services.catalog()


__all__ = ["router", "ASSET_KINDS"]
