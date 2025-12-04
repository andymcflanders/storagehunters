"""API routes for StorageHub."""

from fastapi import APIRouter

from app.api import auth, containers, items, locations, tags, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(locations.router, prefix="/locations", tags=["Locations"])
api_router.include_router(containers.router, prefix="/containers", tags=["Containers"])
api_router.include_router(items.router, prefix="/items", tags=["Items"])
api_router.include_router(tags.router, prefix="/tags", tags=["Tags"])
