import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from drm_document_service.exceptions import DocumentServiceError

logger = logging.getLogger(__name__)


async def document_service_exception_handler(
    request: Request,
    exc: DocumentServiceError,
) -> JSONResponse:
    logger.error(
        "Document service error: %s - Path: %s %s",
        exc.message,
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "status_code": exc.status_code,
        },
    )


async def general_exception_handler(request: Request, _exc: Exception) -> JSONResponse:
    logger.exception(
        "Unexpected error occurred - Path: %s %s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "status_code": 500,
        },
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        DocumentServiceError,
        document_service_exception_handler,
    )
    app.add_exception_handler(Exception, general_exception_handler)
