from fastapi import APIRouter

api_router = APIRouter()

from nutrition_multiagents.api.v1.endpoints import profile

api_router.include_router(profile.router, prefix="/user", tags=["profile"])

