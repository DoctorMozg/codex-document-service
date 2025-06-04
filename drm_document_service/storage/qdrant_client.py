from typing import cast

from qdrant_client import AsyncQdrantClient
from qdrant_client.conversions.common_types import (
    CollectionsResponse,
    ScoredPoint,
    VersionInfo,
)
from qdrant_client.models import CollectionInfo, PointStruct, VectorParams


class QdrantClient:
    def __init__(self, host: str, port: int) -> None:
        self._client = AsyncQdrantClient(host=host, grpc_port=port, prefer_grpc=True)

    async def info(self) -> VersionInfo:
        return await self._client.info()

    async def get_collections(self) -> CollectionsResponse:
        return await self._client.get_collections()

    async def get_collection(self, collection_name: str) -> CollectionInfo:
        return await self._client.get_collection(collection_name)

    async def create_collection(
        self,
        collection_name: str,
        vectors_config: VectorParams,
    ) -> None:
        await self._client.create_collection(
            collection_name=collection_name,
            vectors_config=vectors_config,
        )

    async def upsert(
        self,
        collection_name: str,
        points: list[PointStruct],
    ) -> None:
        await self._client.upsert(
            collection_name=collection_name,
            points=points,
        )

    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int,
    ) -> list[ScoredPoint]:
        return cast(
            list[ScoredPoint],
            await self._client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
            ),
        )
