from drm_document_service.app import app
from drm_document_service.config import config

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=config.host, port=config.port)
