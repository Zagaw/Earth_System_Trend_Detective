from fastapi import APIRouter

from app.api.routes import case_files, climate, export, health, impact, maps, metadata, trends

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(metadata.router, tags=["metadata"])
api_router.include_router(climate.router, tags=["climate"])
api_router.include_router(trends.router, tags=["trends"])
api_router.include_router(maps.router, tags=["geography"])
api_router.include_router(impact.router, tags=["impact"])
api_router.include_router(case_files.router, tags=["case-files"])
api_router.include_router(export.router, tags=["export"])
