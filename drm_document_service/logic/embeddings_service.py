import asyncio
import logging

from openai import AsyncOpenAI
from pydantic import TypeAdapter

from drm_document_service.config import AppConfigSchema
from drm_document_service.schemas import (
    DocumentPartSchema,
    EmbeddedDocumentPartSchema,
    Embeddings,
)

logger = logging.getLogger(__name__)


class EmbeddingsService:
    def __init__(self, config: AppConfigSchema) -> None:
        self.config = config
        self.client = AsyncOpenAI(api_key=config.openai_api_key)

    async def embed_document_part(
        self,
        part: DocumentPartSchema,
    ) -> EmbeddedDocumentPartSchema:
        embedding = await self.generate_embedding(part.text)
        return EmbeddedDocumentPartSchema(
            uid=part.uid,
            document_uid=part.document_uid,
            text=part.text,
            embedding=embedding,
        )

    async def embed_document_parts(
        self,
        parts: list[DocumentPartSchema],
    ) -> list[EmbeddedDocumentPartSchema]:
        tasks = [self.embed_document_part(part) for part in parts]
        return await asyncio.gather(*tasks)

    async def generate_embedding(self, text: str) -> Embeddings:
        try:
            response = await self.client.embeddings.create(
                model=self.config.openai_embedding_model,
                input=text,
            )
            return TypeAdapter(Embeddings).validate_python(response.data[0].embedding)
        except Exception:
            logger.exception("Failed to generate embedding")
            raise
