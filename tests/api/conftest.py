from io import BytesIO
from typing import Any
from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from drm_document_service.agents.pipeline import DocumentPipeline
from drm_document_service.app import create_app
from drm_document_service.logic.embeddings_service import EmbeddingsService
from drm_document_service.logic.pdf_parser_service import PdfParserService
from drm_document_service.schemas import OrchestratorResultSchema, SourceSchema
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
def valid_pdf_upload(sample_pdf_content: bytes) -> dict[str, Any]:
    return {
        "file": ("test.pdf", BytesIO(sample_pdf_content), "application/pdf"),
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
