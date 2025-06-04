from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from drm_document_service import deps
from drm_document_service.schemas import OrchestratorResultSchema


def test_query_documents_success(
    test_app: FastAPI,
    client: TestClient,
    mock_document_pipeline: MagicMock,
    sample_query_result: OrchestratorResultSchema,
) -> None:
    mock_document_pipeline.process_query = AsyncMock(return_value=sample_query_result)
    test_app.dependency_overrides[deps.get_document_pipeline] = (
        lambda: mock_document_pipeline
    )

    query_data = {"question": "What is this document about?"}
    response = client.post("/api/v1/query", json=query_data)

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "This is a sample answer to the query."
    assert data["is_relevant"] is True
    assert data["confidence"] == 0.95
    assert data["query"] == "What is this document about?"
    assert len(data["sources"]) == 1
    assert data["sources"][0]["document_name"] == "test_document.pdf"

    mock_document_pipeline.process_query.assert_called_once_with(
        "What is this document about?",
    )


def test_query_documents_empty_question(
    test_app: FastAPI,
    client: TestClient,
) -> None:
    query_data = {"question": ""}
    response = client.post("/api/v1/query", json=query_data)

    assert response.status_code == 422


def test_query_documents_missing_question(
    test_app: FastAPI,
    client: TestClient,
) -> None:
    query_data: dict[str, str] = {}
    response = client.post("/api/v1/query", json=query_data)

    assert response.status_code == 422


def test_query_documents_invalid_json(
    test_app: FastAPI,
    client: TestClient,
) -> None:
    response = client.post(
        "/api/v1/query",
        data="invalid json",
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 422


def test_query_documents_processing_error(
    test_app: FastAPI,
    client: TestClient,
    mock_document_pipeline: MagicMock,
) -> None:
    mock_document_pipeline.process_query = AsyncMock(
        side_effect=Exception("Pipeline error"),
    )
    test_app.dependency_overrides[deps.get_document_pipeline] = (
        lambda: mock_document_pipeline
    )

    query_data = {"question": "What is this document about?"}
    response = client.post("/api/v1/query", json=query_data)

    assert response.status_code == 500
    assert "Query processing failed" in response.json()["message"]


@pytest.mark.parametrize(
    "question",
    [
        "What is the main topic?",
        "Summarize the document",
        "What are the key points mentioned?",
    ],
)
def test_query_documents_various_questions(
    test_app: FastAPI,
    client: TestClient,
    mock_document_pipeline: MagicMock,
    sample_query_result: OrchestratorResultSchema,
    question: str,
) -> None:
    mock_document_pipeline.process_query = AsyncMock(return_value=sample_query_result)
    test_app.dependency_overrides[deps.get_document_pipeline] = (
        lambda: mock_document_pipeline
    )

    query_data = {"question": question}
    response = client.post("/api/v1/query", json=query_data)

    assert response.status_code == 200
    mock_document_pipeline.process_query.assert_called_with(question)


def test_query_documents_no_relevant_results(
    test_app: FastAPI,
    client: TestClient,
    mock_document_pipeline: MagicMock,
) -> None:
    irrelevant_result = OrchestratorResultSchema(
        answer="I couldn't find relevant information about that topic.",
        sources=[],
        is_relevant=False,
        confidence=0.1,
        query="Irrelevant question",
    )
    mock_document_pipeline.process_query = AsyncMock(return_value=irrelevant_result)
    test_app.dependency_overrides[deps.get_document_pipeline] = (
        lambda: mock_document_pipeline
    )

    query_data = {"question": "Irrelevant question"}
    response = client.post("/api/v1/query", json=query_data)

    assert response.status_code == 200
    data = response.json()
    assert data["is_relevant"] is False
    assert data["confidence"] == 0.1
    assert len(data["sources"]) == 0
