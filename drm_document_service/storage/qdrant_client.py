import logging
from typing import cast

from qdrant_client import AsyncQdrantClient
from qdrant_client.conversions.common_types import (
    CollectionsResponse,
    ScoredPoint,
    VersionInfo,
)
from qdrant_client.models import CollectionInfo, PointStruct, VectorParams

logger = logging.getLogger(__name__)


class QdrantClient:
    def __init__(self, host: str, port: int) -> None:
        logger.info("Initializing QdrantClient with host: %s, port: %d", host, port)
        self._client = AsyncQdrantClient(host=host, grpc_port=port, prefer_grpc=True)

    async def info(self) -> VersionInfo:
        logger.debug("Getting Qdrant version info")
        result = await self._client.info()
        logger.debug("Successfully retrieved Qdrant version info")
        return result

    async def get_collections(self) -> CollectionsResponse:
        logger.debug("Getting all collections")
        result = await self._client.get_collections()
        logger.debug("Successfully retrieved collections")
        return result

    async def get_collection(self, collection_name: str) -> CollectionInfo:
        logger.debug("Getting collection: %s", collection_name)
        result = await self._client.get_collection(collection_name)
        logger.debug("Successfully retrieved collection: %s", collection_name)
        return result

    async def create_collection(
        self,
        collection_name: str,
        vectors_config: VectorParams,
    ) -> None:
        logger.info("Creating collection: %s", collection_name)
        await self._client.create_collection(
            collection_name=collection_name,
            vectors_config=vectors_config,
        )
        logger.info("Successfully created collection: %s", collection_name)

    async def upsert(
        self,
        collection_name: str,
        points: list[PointStruct],
    ) -> None:
        logger.debug(
            "Upserting %d points to collection: %s",
            len(points),
            collection_name,
        )
        await self._client.upsert(
            collection_name=collection_name,
            points=points,
        )
        logger.debug(
            "Successfully upserted %d points to collection: %s",
            len(points),
            collection_name,
        )

    async def search(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int,
    ) -> list[ScoredPoint]:
        logger.debug("Searching collection: %s with limit: %d", collection_name, limit)
        result = cast(
            list[ScoredPoint],
            await self._client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
            ),
        )
        logger.debug(
            "Successfully searched collection: %s, found %d results",
            collection_name,
            len(result),
        )
        return result
