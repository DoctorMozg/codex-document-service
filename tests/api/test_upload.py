from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from drm_document_service import deps
from drm_document_service.schemas import DocumentPartSchema, EmbeddedDocumentPartSchema


def test_upload_pdf_successful_upload(
    test_app: FastAPI,
    client: TestClient,
    mock_document_repository: MagicMock,
    mock_embeddings_repository: MagicMock,
    mock_embeddings_service: MagicMock,
    mock_pdf_parser_service: MagicMock,
    valid_pdf_upload: dict[str, Any],
    sample_document_part: DocumentPartSchema,
    sample_embedded_part: EmbeddedDocumentPartSchema,
) -> None:
    mock_pdf_parser_service.parse_document.return_value = [sample_document_part]
    mock_embeddings_service.embed_document_parts = AsyncMock(
        return_value=[sample_embedded_part],
    )
    mock_document_repository.save_document = AsyncMock()
    mock_embeddings_repository.store_embeddings = AsyncMock()

    test_app.dependency_overrides[deps.get_document_repository] = (
        lambda: mock_document_repository
    )
    test_app.dependency_overrides[deps.get_embeddings_repository] = (
        lambda: mock_embeddings_repository
    )
    test_app.dependency_overrides[deps.get_embeddings_service] = (
        lambda: mock_embeddings_service
    )
    test_app.dependency_overrides[deps.get_pdf_parser_service] = (
        lambda: mock_pdf_parser_service
    )

    response = client.post("/api/v1/upload", files=valid_pdf_upload)

    assert response.status_code == 200
    data = response.json()
    assert "document_uid" in data
    assert data["filename"] == "test.pdf"
    assert "Successfully uploaded and processed 1 parts" in data["message"]

    mock_document_repository.save_document.assert_called_once()
    mock_pdf_parser_service.parse_document.assert_called_once()
    mock_embeddings_service.embed_document_parts.assert_called_once()
    mock_embeddings_repository.store_embeddings.assert_called_once()


def test_upload_pdf_invalid_file_type(
    test_app: FastAPI,
    client: TestClient,
    invalid_file_upload: dict[str, Any],
) -> None:
    response = client.post("/api/v1/upload", files=invalid_file_upload)

    assert response.status_code == 400
    assert "Invalid file type" in response.json()["message"]


@pytest.mark.parametrize(
    "filename",
    [
        "test.txt",
        "document.doc",
        "image.png",
        "test.PDF",
    ],
)
def test_upload_pdf_invalid_file_extensions(
    test_app: FastAPI,
    client: TestClient,
    filename: str,
) -> None:
    files = {"file": (filename, b"content", "application/octet-stream")}
    response = client.post("/api/v1/upload", files=files)

    assert response.status_code == 400
    assert "Invalid file type" in response.json()["message"]


def test_upload_pdf_file_too_large(
    test_app: FastAPI,
    client: TestClient,
    large_pdf_upload: dict[str, Any],
) -> None:
    response = client.post("/api/v1/upload", files=large_pdf_upload)

    assert response.status_code == 413
    assert "File too large" in response.json()["message"]


def test_upload_pdf_processing_error(
    test_app: FastAPI,
    client: TestClient,
    mock_document_repository: MagicMock,
    mock_embeddings_repository: MagicMock,
    mock_embeddings_service: MagicMock,
    mock_pdf_parser_service: MagicMock,
    valid_pdf_upload: dict[str, Any],
) -> None:
    mock_document_repository.save_document = AsyncMock(
        side_effect=Exception("Storage error"),
    )

    test_app.dependency_overrides[deps.get_document_repository] = (
        lambda: mock_document_repository
    )
    test_app.dependency_overrides[deps.get_embeddings_repository] = (
        lambda: mock_embeddings_repository
    )
    test_app.dependency_overrides[deps.get_embeddings_service] = (
        lambda: mock_embeddings_service
    )
    test_app.dependency_overrides[deps.get_pdf_parser_service] = (
        lambda: mock_pdf_parser_service
    )

    response = client.post("/api/v1/upload", files=valid_pdf_upload)

    assert response.status_code == 500
    assert "Document processing failed" in response.json()["message"]


def test_upload_pdf_parsing_error(
    test_app: FastAPI,
    client: TestClient,
    mock_document_repository: MagicMock,
    mock_embeddings_repository: MagicMock,
    mock_embeddings_service: MagicMock,
    mock_pdf_parser_service: MagicMock,
    valid_pdf_upload: dict[str, Any],
) -> None:
    mock_document_repository.save_document = AsyncMock()
    mock_pdf_parser_service.parse_document.side_effect = Exception("PDF parsing error")

    test_app.dependency_overrides[deps.get_document_repository] = (
        lambda: mock_document_repository
    )
    test_app.dependency_overrides[deps.get_embeddings_repository] = (
        lambda: mock_embeddings_repository
    )
    test_app.dependency_overrides[deps.get_embeddings_service] = (
        lambda: mock_embeddings_service
    )
    test_app.dependency_overrides[deps.get_pdf_parser_service] = (
        lambda: mock_pdf_parser_service
    )

    response = client.post("/api/v1/upload", files=valid_pdf_upload)

    assert response.status_code == 500
    assert "Document processing failed" in response.json()["message"]


def test_upload_pdf_embeddings_error(
    test_app: FastAPI,
    client: TestClient,
    mock_document_repository: MagicMock,
    mock_embeddings_repository: MagicMock,
    mock_embeddings_service: MagicMock,
    mock_pdf_parser_service: MagicMock,
    valid_pdf_upload: dict[str, Any],
    sample_document_part: DocumentPartSchema,
) -> None:
    mock_document_repository.save_document = AsyncMock()
    mock_pdf_parser_service.parse_document.return_value = [sample_document_part]
    mock_embeddings_service.embed_document_parts = AsyncMock(
        side_effect=Exception("Embeddings error"),
    )

    test_app.dependency_overrides[deps.get_document_repository] = (
        lambda: mock_document_repository
    )
    test_app.dependency_overrides[deps.get_embeddings_repository] = (
        lambda: mock_embeddings_repository
    )
    test_app.dependency_overrides[deps.get_embeddings_service] = (
        lambda: mock_embeddings_service
    )
    test_app.dependency_overrides[deps.get_pdf_parser_service] = (
        lambda: mock_pdf_parser_service
    )

    response = client.post("/api/v1/upload", files=valid_pdf_upload)

    assert response.status_code == 500
    assert "Document processing failed" in response.json()["message"]
