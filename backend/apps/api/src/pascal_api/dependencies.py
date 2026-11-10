"""Shared FastAPI dependencies. Routers take what they need with Depends(); tests swap them through `app.dependency_overrides` or by building the app with other settings."""
from pathlib import Path

from fastapi import Depends, Request

from .auth.identity import current_user
from .config import Settings
from .storage.jobs import JobStore
from .storage.projects import ProjectStore


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def _user_stores(request: Request, user_id: str):
    state = request.app.state
    with state.user_stores_lock:
        if user_id not in state.user_stores:
            root = state.settings.data_dir / "users" / user_id
            state.user_stores[user_id] = (ProjectStore(root), JobStore(root, state.settings.workers))
        return state.user_stores[user_id]


def get_store(request: Request, user_id: str | None = Depends(current_user)) -> ProjectStore:
    return _user_stores(request, user_id)[0] if user_id else request.app.state.store


def get_jobs(request: Request, user_id: str | None = Depends(current_user)) -> JobStore:
    return _user_stores(request, user_id)[1] if user_id else request.app.state.jobs


def get_llm(request: Request):
    return request.app.state.llm_runner


def get_analysis_llm(request: Request):
    return request.app.state.analysis_runner


def project_dir(pid: str, store: ProjectStore = Depends(get_store)) -> Path:
    """Path parameter {pid} -> an existing, validated project folder (400 bad id, 404 unknown)."""
    return store.dir(pid)
