from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from drm_document_service.api import api_router
from drm_document_service.error_handlers import register_error_handlers
from drm_document_service.logger import setup_logging


def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title="Document RAG Service",
        description="A service for intelligent querying of documents",
        version="1.0.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)

    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "healthy", "service": "document-rag-service"}

    return app


app = create_app()
