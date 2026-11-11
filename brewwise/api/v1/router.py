from fastapi import APIRouter
from brewwise.api.v1.health import router as health_router
from brewwise.api.v1.scan import router as scan_router
from brewwise.api.v1.recipes import router as recipe_router
from brewwise.api.v1.equipment import router as equipment_router
from brewwise.api.v1.auth import router as auth_router
from brewwise.api.v1.brews import router as brews_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(health_router)
api_v1_router.include_router(scan_router)
api_v1_router.include_router(recipe_router)
api_v1_router.include_router(equipment_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(brews_router)
