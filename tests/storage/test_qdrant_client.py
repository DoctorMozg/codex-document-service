from typing import Any

import pytest

from drm_document_service.storage.qdrant_client import QdrantClient
from tests.conftest import QdrantConfig


@pytest.fixture
def qdrant_client(qdrant_container: QdrantConfig) -> QdrantClient:
    return QdrantClient(
        host=qdrant_container["host"],
        port=qdrant_container["port"],
    )


@pytest.mark.asyncio
async def test_client_connection(qdrant_client: QdrantClient) -> None:
    info: Any = await qdrant_client.info()
    assert info is not None


@pytest.mark.asyncio
async def test_client_collections_list(qdrant_client: QdrantClient) -> None:
    collections: Any = await qdrant_client.get_collections()
    assert collections is not None
    assert hasattr(collections, "collections")
