from fastapi import APIRouter

from ..gateways import agents

router = APIRouter(tags=["catalog"])


@router.get("/catalog")
def get_catalog():
    """Roles, page flags, grid systems, compositions, photo-set templates, exporter backends: what a book plan may use."""
    return agents.catalog()
