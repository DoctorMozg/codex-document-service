from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_create_app_returns_fastapi_instance(test_app: FastAPI) -> None:
    assert isinstance(test_app, FastAPI)
    assert test_app.title == "Document RAG Service"
    assert test_app.description == "A service for intelligent querying of documents"
    assert test_app.version == "1.0.0"


def test_health_check_returns_correct_status(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "document-rag-service",
    }
