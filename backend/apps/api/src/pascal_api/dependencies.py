"""Shared FastAPI dependencies. Routers take what they need with Depends(); tests swap them through `app.dependency_overrides` or by building the app with other settings."""
from pathlib import Path

from fastapi import Depends, Request

from .config import Settings
from .storage.jobs import JobStore
from .storage.projects import ProjectStore


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_store(request: Request) -> ProjectStore:
    return request.app.state.store


def get_jobs(request: Request) -> JobStore:
    return request.app.state.jobs


def get_llm(request: Request):
    return request.app.state.llm_runner


def get_analysis_llm(request: Request):
    return request.app.state.analysis_runner


def project_dir(pid: str, store: ProjectStore = Depends(get_store)) -> Path:
    """Path parameter {pid} -> an existing, validated project folder (400 bad id, 404 unknown)."""
    return store.dir(pid)
