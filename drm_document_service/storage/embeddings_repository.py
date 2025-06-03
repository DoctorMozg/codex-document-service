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
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name

    async def ensure_collection_exists(self) -> None:
        try:
            await self.qdrant_client._client.get_collection(self.collection_name)
        except Exception:
            await self.qdrant_client._client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
            )

    async def store_embedding(self, embedded_part: EmbeddedDocumentPartSchema) -> None:
        await self.ensure_collection_exists()

        point = models.PointStruct(
            id=str(embedded_part.uid),
            vector=embedded_part.embedding,
            payload={
                "document_uid": str(embedded_part.document_uid),
                "text": embedded_part.text,
            },
        )

        await self.qdrant_client._client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )

    async def store_embeddings(
        self,
        embedded_parts: list[EmbeddedDocumentPartSchema],
    ) -> None:
        if not embedded_parts:
            return

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

        await self.qdrant_client._client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

    async def search_similar(
        self,
        query_embedding: Embeddings,
        limit: int = 10,
    ) -> list[SearchResultSchema]:
        try:
            results = await self.qdrant_client._client.search(
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

            return search_results
        except Exception:
            logger.exception("Failed to search similar embeddings")
            return []
