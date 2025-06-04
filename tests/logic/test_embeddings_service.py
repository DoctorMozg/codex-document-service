from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest

from drm_document_service.logic.embeddings_service import EmbeddingsService
from drm_document_service.schemas import DocumentPartSchema, EmbeddedDocumentPartSchema


@pytest.fixture
def embeddings_service(mock_config, monkeypatch):
    service = EmbeddingsService(mock_config)

    mock_client = Mock()
    mock_response = Mock()
    mock_response.data = [Mock()]
    mock_response.data[0].embedding = [0.1] * 1536

    mock_client.embeddings.create = AsyncMock(return_value=mock_response)
    monkeypatch.setattr(service, "client", mock_client)

    return service


@pytest.mark.asyncio
async def test_generate_embedding(embeddings_service):
    result = await embeddings_service.generate_embedding("test text")

    assert len(result) == 1536
    assert all(isinstance(x, float) for x in result)


@pytest.mark.asyncio
async def test_embed_document_part(embeddings_service, sample_document_part):
    result = await embeddings_service.embed_document_part(sample_document_part)

    assert isinstance(result, EmbeddedDocumentPartSchema)
    assert result.uid == sample_document_part.uid
    assert result.document_uid == sample_document_part.document_uid
    assert result.text == sample_document_part.text
    assert len(result.embedding) == 1536


@pytest.mark.asyncio
async def test_embed_document_parts(embeddings_service):
    parts = [
        DocumentPartSchema(
            uid=uuid4(),
            document_uid=uuid4(),
            text=f"Sample text {i}",
        )
        for i in range(3)
    ]

    results = await embeddings_service.embed_document_parts(parts)

    assert len(results) == 3
    assert all(isinstance(r, EmbeddedDocumentPartSchema) for r in results)
    assert all(len(r.embedding) == 1536 for r in results)
