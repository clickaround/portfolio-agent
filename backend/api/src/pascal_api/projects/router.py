from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse

from ..config import Settings
from ..dependencies import get_settings, get_store, project_dir
from ..storage.projects import ProjectStore
from . import service
from .schemas import AssetInfo, BriefBody, ManifestOut, ProjectCreate, ProjectInfo

router = APIRouter(tags=["projects"])


@router.get("/projects", response_model=list[ProjectInfo])
def list_projects(store: ProjectStore = Depends(get_store)):
    return store.list()


@router.post("/projects", status_code=201, response_model=ProjectInfo)
def create_project(body: ProjectCreate, store: ProjectStore = Depends(get_store)):
    store.create(body.id, body.title, body.brief)
    return store.meta(body.id)


@router.get("/projects/{pid}", response_model=ProjectInfo)
def get_project(pid: str, store: ProjectStore = Depends(get_store)):
    return store.meta(pid)


@router.delete("/projects/{pid}", status_code=204)
def delete_project(pid: str, store: ProjectStore = Depends(get_store)):
    store.delete(pid)


@router.get("/projects/{pid}/brief", response_model=BriefBody)
def get_brief(d: Path = Depends(project_dir)):
    return {"markdown": service.read_brief(d)}


@router.put("/projects/{pid}/brief")
def put_brief(body: BriefBody, d: Path = Depends(project_dir)):
    return {"bytes": service.write_brief(d, body.markdown)}


@router.get("/projects/{pid}/manifest", response_model=ManifestOut)
def get_manifest(d: Path = Depends(project_dir)):
    return service.manifest(d)


@router.post("/projects/{pid}/assets/{kind}", status_code=201, response_model=AssetInfo)
def upload_asset(pid: str, kind: str, file: UploadFile = File(...), store: ProjectStore = Depends(get_store), settings: Settings = Depends(get_settings)):
    """kind = images | drawings | diagrams. The file name becomes the asset id (stem)."""
    p = store.add_asset(pid, kind, file.filename or "", file.file, settings.max_upload_mb * (1 << 20))
    return {"kind": kind, "file": p.name, "id": p.stem}


@router.delete("/projects/{pid}/assets/{kind}/{name}", status_code=204)
def delete_asset(pid: str, kind: str, name: str, store: ProjectStore = Depends(get_store)):
    store.asset_path(pid, kind, name).unlink()


@router.get("/projects/{pid}/files/{kind}/{name}")
def get_file(pid: str, kind: str, name: str, store: ProjectStore = Depends(get_store)):
    """Original or derived file (kind = images | drawings | diagrams | sources)."""
    return FileResponse(store.asset_path(pid, kind, name))
