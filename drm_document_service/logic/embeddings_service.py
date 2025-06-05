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
        logger.debug(
            "Initializing EmbeddingsService with model: %s",
            config.openai_embedding_model,
        )
        self.config = config
        self.client = AsyncOpenAI(api_key=config.openai_api_key)

    async def embed_document_part(
        self,
        part: DocumentPartSchema,
    ) -> EmbeddedDocumentPartSchema:
        logger.debug(
            "Embedding document part: %s (text length: %d)",
            part.uid,
            len(part.text),
        )
        embedding = await self.generate_embedding(part.text)
        result = EmbeddedDocumentPartSchema(
            uid=part.uid,
            document_uid=part.document_uid,
            text=part.text,
            embedding=embedding,
        )
        logger.debug("Successfully embedded document part: %s", part.uid)
        return result

    async def embed_document_parts(
        self,
        parts: list[DocumentPartSchema],
    ) -> list[EmbeddedDocumentPartSchema]:
        logger.info("Embedding %d document parts", len(parts))
        tasks = [self.embed_document_part(part) for part in parts]
        results = await asyncio.gather(*tasks)
        logger.info("Successfully embedded %d document parts", len(results))
        return results

    async def generate_embedding(self, text: str) -> Embeddings:
        logger.debug("Generating embedding for text length: %d characters", len(text))
        try:
            response = await self.client.embeddings.create(
                model=self.config.openai_embedding_model,
                input=text,
            )
            result = TypeAdapter(Embeddings).validate_python(response.data[0].embedding)
            logger.debug(
                "Successfully generated embedding (dimension: %d)",
                len(result),
            )
        except Exception:
            logger.exception(
                "Failed to generate embedding for text length: %d",
                len(text),
            )
            raise
        else:
            return result
