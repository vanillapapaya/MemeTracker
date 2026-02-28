from fastapi import APIRouter

from app.api import health, search, images, feed

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router, tags=["health"])
api_router.include_router(search.router, tags=["search"])
api_router.include_router(images.router, tags=["images"])
api_router.include_router(feed.router, tags=["feed"])
