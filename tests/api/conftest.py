from io import BytesIO
from typing import Any
from unittest.mock import MagicMock, create_autospec
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from drm_document_service.agents.pipeline import DocumentPipeline
from drm_document_service.app import create_app
from drm_document_service.logic.embeddings_service import EmbeddingsService
from drm_document_service.logic.pdf_parser_service import PdfParserService
from drm_document_service.schemas import (
    DocumentInfoSchema,
    DocumentPartSchema,
    DocumentSchema,
    EmbeddedDocumentPartSchema,
    OrchestratorResultSchema,
    SourceSchema,
)
from drm_document_service.storage.document_repository import DocumentRepository
from drm_document_service.storage.embeddings_repository import EmbeddingsRepository


@pytest.fixture
def test_app() -> FastAPI:
    return create_app()


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    return TestClient(test_app)


@pytest.fixture
def mock_document_repository() -> MagicMock:
    return create_autospec(DocumentRepository, instance=True)  # type: ignore


@pytest.fixture
def mock_embeddings_repository() -> MagicMock:
    return create_autospec(EmbeddingsRepository, instance=True)  # type: ignore


@pytest.fixture
def mock_embeddings_service() -> MagicMock:
    return create_autospec(EmbeddingsService, instance=True)  # type: ignore


@pytest.fixture
def mock_pdf_parser_service() -> MagicMock:
    return create_autospec(PdfParserService, instance=True)  # type: ignore


@pytest.fixture
def mock_document_pipeline() -> MagicMock:
    return create_autospec(DocumentPipeline, instance=True)  # type: ignore


@pytest.fixture
def sample_document_uid() -> UUID:
    return uuid4()


@pytest.fixture
def sample_pdf_content() -> bytes:
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj"


@pytest.fixture
def sample_document_schema(sample_document_uid: UUID) -> DocumentSchema:
    return DocumentSchema(
        uid=sample_document_uid,
        name="test_document.pdf",
        body_bytes=b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj",
    )


@pytest.fixture
def sample_document_info(sample_document_uid: UUID) -> DocumentInfoSchema:
    return DocumentInfoSchema(
        uid=sample_document_uid,
        name="test_document.pdf",
        upload_date="2024-01-01T12:00:00",
        size_bytes=1024,
    )


@pytest.fixture
def sample_document_part(sample_document_uid: UUID) -> DocumentPartSchema:
    return DocumentPartSchema(
        uid=uuid4(),
        document_uid=sample_document_uid,
        text="This is a sample document part content.",
    )


@pytest.fixture
def sample_embedded_part(
    sample_document_part: DocumentPartSchema,
) -> EmbeddedDocumentPartSchema:
    return EmbeddedDocumentPartSchema(
        uid=sample_document_part.uid,
        document_uid=sample_document_part.document_uid,
        text=sample_document_part.text,
        embedding=[0.1] * 1536,
    )


@pytest.fixture
def sample_query_result() -> OrchestratorResultSchema:
    return OrchestratorResultSchema(
        answer="This is a sample answer to the query.",
        sources=[
            SourceSchema(
                document_name="test_document.pdf",
                document_uid=uuid4(),
                part_uid=uuid4(),
                text_snippet="Sample text snippet",
                relevance_score=0.95,
            ),
        ],
        is_relevant=True,
        confidence=0.95,
        query="What is this document about?",
    )


@pytest.fixture
def valid_pdf_upload() -> dict[str, Any]:
    pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj"
    return {
        "file": ("test.pdf", BytesIO(pdf_content), "application/pdf"),
    }


@pytest.fixture
def invalid_file_upload() -> dict[str, Any]:
    return {
        "file": ("test.txt", BytesIO(b"This is not a PDF"), "text/plain"),
    }


@pytest.fixture
def large_pdf_upload() -> dict[str, Any]:
    large_content = b"%PDF-1.4\n" + b"x" * (50 * 1024 * 1024)
    return {
        "file": ("large.pdf", BytesIO(large_content), "application/pdf"),
    }
