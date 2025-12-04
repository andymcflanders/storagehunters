"""API routes for StorageHub."""

from fastapi import APIRouter

from app.api import (
    activity,
    auth,
    containers,
    export,
    items,
    locations,
    printers,
    search,
    tags,
    users,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(locations.router, prefix="/locations", tags=["Locations"])
api_router.include_router(containers.router, prefix="/containers", tags=["Containers"])
api_router.include_router(items.router, prefix="/items", tags=["Items"])
api_router.include_router(tags.router, prefix="/tags", tags=["Tags"])
api_router.include_router(search.router, prefix="/search", tags=["Search"])
api_router.include_router(printers.router, prefix="/printers", tags=["Printers"])
api_router.include_router(activity.router, prefix="/activity", tags=["Activity"])
api_router.include_router(export.router, prefix="/export", tags=["Export"])
