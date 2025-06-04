import logging
from dataclasses import dataclass
from typing import cast

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel

from drm_document_service.agents.template_manager import (
    TemplateContextSchema,
    TemplateManager,
)
from drm_document_service.logic.embeddings_service import EmbeddingsService
from drm_document_service.schemas import RetrievalResultSchema, SearchResultSchema
from drm_document_service.storage.embeddings_repository import EmbeddingsRepository

logger = logging.getLogger(__name__)


@dataclass
class RetrievalDepsSchema:
    embeddings_service: EmbeddingsService
    embeddings_repository: EmbeddingsRepository


async def _semantic_search_tool(
    ctx: RunContext[RetrievalDepsSchema],
    query: str,
) -> list[SearchResultSchema]:
    """
    Perform semantic search to find relevant document parts based on a query.

    This tool generates an embedding for the input query and searches for similar
    document parts in the embeddings repository. It returns the most relevant
    document parts that match the semantic meaning of the query.

    Args:
        query: The search query text to find relevant document parts

    Returns:
        A list of SearchResultSchema objects containing the most relevant
        document parts, limited to 10 results. Returns empty list if search fails.
    """
    try:
        query_embedding = await ctx.deps.embeddings_service.generate_embedding(query)

        return cast(
            list[SearchResultSchema],
            await ctx.deps.embeddings_repository.search_similar(
                query_embedding=query_embedding,
                limit=10,
            ),
        )

    except Exception:
        logger.exception("Failed to perform semantic search")
        return []


def get_retrieval_agent(
    model: OpenAIModel,
    template_manager: TemplateManager,
    template_context: TemplateContextSchema | None = None,
) -> Agent[RetrievalDepsSchema, RetrievalResultSchema]:
    if template_context is None:
        template_context = TemplateContextSchema()  # type: ignore

    system_prompt = template_manager.render_template(
        "retrieval_system_prompt.j2",
        template_context,
    )

    return Agent(
        model=model,
        deps_type=RetrievalDepsSchema,
        output_type=RetrievalResultSchema,
        system_prompt=system_prompt,
        tools=[_semantic_search_tool],
    )
