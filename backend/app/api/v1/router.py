from fastapi import APIRouter

from app.api.v1 import auth, health, repositories

api_v1_router = APIRouter()
api_v1_router.include_router(health.router, tags=["health"])
api_v1_router.include_router(auth.router, tags=["auth"])
api_v1_router.include_router(repositories.router, tags=["repositories"])
