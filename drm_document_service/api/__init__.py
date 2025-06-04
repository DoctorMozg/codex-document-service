from fastapi import APIRouter

from drm_document_service.api import file, query, upload

api_router = APIRouter()

api_router.include_router(query.router, tags=["Query"])
api_router.include_router(upload.router, tags=["Upload"])
api_router.include_router(file.router, tags=["Files"])
