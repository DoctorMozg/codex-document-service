from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient

from drm_document_service import deps
from drm_document_service.schemas import DocumentInfoSchema, DocumentSchema


def test_list_documents_success(
    test_app: FastAPI,
    client: TestClient,
    mock_document_repository: MagicMock,
    sample_document_info: DocumentInfoSchema,
) -> None:
    mock_document_repository.list_documents = AsyncMock(
        return_value=[sample_document_info],
    )
    test_app.dependency_overrides[deps.get_document_repository] = (
        lambda: mock_document_repository
    )

    response = client.get("/api/v1/documents")

    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total_count" in data
    assert data["total_count"] == 1
    assert len(data["documents"]) == 1
    assert data["documents"][0]["name"] == "test_document.pdf"


def test_list_documents_empty(
    test_app: FastAPI,
    client: TestClient,
    mock_document_repository: MagicMock,
) -> None:
    mock_document_repository.list_documents = AsyncMock(return_value=[])
    test_app.dependency_overrides[deps.get_document_repository] = (
        lambda: mock_document_repository
    )

    response = client.get("/api/v1/documents")

    assert response.status_code == 200
    data = response.json()
    assert data["documents"] == []
    assert data["total_count"] == 0


def test_get_document_info_success(
    test_app: FastAPI,
    client: TestClient,
    mock_document_repository: MagicMock,
    sample_document_uid: UUID,
    sample_document_info: DocumentInfoSchema,
) -> None:
    mock_document_repository.get_document_info = AsyncMock(
        return_value=sample_document_info,
    )
    test_app.dependency_overrides[deps.get_document_repository] = (
        lambda: mock_document_repository
    )

    response = client.get(f"/api/v1/documents/{sample_document_uid}/info")

    assert response.status_code == 200
    data = response.json()
    assert data["uid"] == str(sample_document_uid)
    assert data["name"] == "test_document.pdf"
    assert data["upload_date"] == "2024-01-01T12:00:00"
    assert data["size_bytes"] == 1024


def test_get_document_info_not_found(
    test_app: FastAPI,
    client: TestClient,
    mock_document_repository: MagicMock,
    sample_document_uid: UUID,
) -> None:
    mock_document_repository.get_document_info = AsyncMock(return_value=None)
    test_app.dependency_overrides[deps.get_document_repository] = (
        lambda: mock_document_repository
    )

    response = client.get(f"/api/v1/documents/{sample_document_uid}/info")

    assert response.status_code == 404
    assert "Document with ID" in response.json()["message"]


def test_get_document_info_invalid_uuid(
    test_app: FastAPI,
    client: TestClient,
) -> None:
    response = client.get("/api/v1/documents/invalid-uuid/info")

    assert response.status_code == 422


def test_download_document_success(
    test_app: FastAPI,
    client: TestClient,
    mock_document_repository: MagicMock,
    sample_document_uid: UUID,
    sample_document_schema: DocumentSchema,
) -> None:
    mock_document_repository.get_document = AsyncMock(
        return_value=sample_document_schema,
    )
    test_app.dependency_overrides[deps.get_document_repository] = (
        lambda: mock_document_repository
    )

    response = client.get(f"/api/v1/documents/{sample_document_uid}/download")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert (
        "attachment; filename=test_document.pdf"
        in response.headers["content-disposition"]
    )
    assert response.content == sample_document_schema.body_bytes


def test_download_document_not_found(
    test_app: FastAPI,
    client: TestClient,
    mock_document_repository: MagicMock,
    sample_document_uid: UUID,
) -> None:
    mock_document_repository.get_document = AsyncMock(return_value=None)
    test_app.dependency_overrides[deps.get_document_repository] = (
        lambda: mock_document_repository
    )

    response = client.get(f"/api/v1/documents/{sample_document_uid}/download")

    assert response.status_code == 404
    assert "Document with ID" in response.json()["message"]


def test_download_document_invalid_uuid(
    test_app: FastAPI,
    client: TestClient,
) -> None:
    response = client.get("/api/v1/documents/invalid-uuid/download")

    assert response.status_code == 422


def test_delete_document_success(
    test_app: FastAPI,
    client: TestClient,
    mock_document_repository: MagicMock,
    sample_document_uid: UUID,
) -> None:
    mock_document_repository.delete_document = AsyncMock(return_value=True)
    test_app.dependency_overrides[deps.get_document_repository] = (
        lambda: mock_document_repository
    )

    response = client.delete(f"/api/v1/documents/{sample_document_uid}")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Document deleted successfully"
    assert data["document_uid"] == str(sample_document_uid)


def test_delete_document_not_found(
    test_app: FastAPI,
    client: TestClient,
    mock_document_repository: MagicMock,
    sample_document_uid: UUID,
) -> None:
    mock_document_repository.delete_document = AsyncMock(return_value=False)
    test_app.dependency_overrides[deps.get_document_repository] = (
        lambda: mock_document_repository
    )

    response = client.delete(f"/api/v1/documents/{sample_document_uid}")

    assert response.status_code == 404
    assert "Document with ID" in response.json()["message"]


def test_delete_document_invalid_uuid(
    test_app: FastAPI,
    client: TestClient,
) -> None:
    response = client.delete("/api/v1/documents/invalid-uuid")

    assert response.status_code == 422
