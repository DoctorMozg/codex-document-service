import logging
from uuid import UUID

from qdrant_client import models
from qdrant_client.models import Distance, VectorParams

from drm_document_service.schemas import (
    EmbeddedDocumentPartSchema,
    Embeddings,
    SearchResultSchema,
)
from drm_document_service.storage.qdrant_client import QdrantClient

logger = logging.getLogger(__name__)


class EmbeddingsRepository:
    def __init__(self, qdrant_client: QdrantClient, collection_name: str) -> None:
        logger.debug(
            "Initializing EmbeddingsRepository with collection: %s",
            collection_name,
        )
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name

    async def ensure_collection_exists(self) -> None:
        logger.debug("Ensuring collection exists: %s", self.collection_name)
        try:
            await self.qdrant_client.get_collection(self.collection_name)
            logger.debug("Collection already exists: %s", self.collection_name)
        except Exception:  # noqa: BLE001
            logger.info("Collection does not exist, creating: %s", self.collection_name)
            await self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
            )
            logger.info("Successfully created collection: %s", self.collection_name)

    async def store_embedding(self, embedded_part: EmbeddedDocumentPartSchema) -> None:
        logger.debug("Storing single embedding for part: %s", embedded_part.uid)
        await self.ensure_collection_exists()

        point = models.PointStruct(
            id=str(embedded_part.uid),
            vector=embedded_part.embedding,
            payload={
                "document_uid": str(embedded_part.document_uid),
                "text": embedded_part.text,
            },
        )

        await self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )
        logger.debug("Successfully stored embedding for part: %s", embedded_part.uid)

    async def store_embeddings(
        self,
        embedded_parts: list[EmbeddedDocumentPartSchema],
    ) -> None:
        if not embedded_parts:
            logger.debug("No embeddings to store")
            return

        logger.info("Storing %d embeddings", len(embedded_parts))
        await self.ensure_collection_exists()

        points = [
            models.PointStruct(
                id=str(part.uid),
                vector=part.embedding,
                payload={
                    "document_uid": str(part.document_uid),
                    "text": part.text,
                },
            )
            for part in embedded_parts
        ]

        await self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=points,
        )
        logger.info("Successfully stored %d embeddings", len(embedded_parts))

    async def search_similar(
        self,
        query_embedding: Embeddings,
        limit: int = 10,
    ) -> list[SearchResultSchema]:
        logger.debug("Searching for similar embeddings with limit: %d", limit)
        try:
            results = await self.qdrant_client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=limit,
            )

            search_results = []
            for result in results:
                document_part = EmbeddedDocumentPartSchema(
                    uid=UUID(result.id),
                    document_uid=UUID(result.payload["document_uid"]),
                    text=result.payload["text"],
                    embedding=query_embedding,
                )
                search_results.append(
                    SearchResultSchema(
                        document_part=document_part,
                        score=result.score,
                    ),
                )

            logger.info("Successfully found %d similar embeddings", len(search_results))
        except Exception:
            logger.exception(
                "Failed to search similar embeddings with limit: %d",
                limit,
            )
            return []
        else:
            return search_results
