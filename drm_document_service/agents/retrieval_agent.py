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


LOG_SHOW_CHARS_MAX = 100


@dataclass
class RetrievalDepsSchema:
    embeddings_service: EmbeddingsService
    embeddings_repository: EmbeddingsRepository
    max_results: int = 3
    max_text_length: int = 1000


def _truncate_text(text: str, max_length: int = 1000) -> str:
    if len(text) <= max_length:
        return text

    truncated = text[:max_length]
    last_space = truncated.rfind(" ")

    if last_space > max_length * 0.8:
        return truncated[:last_space] + "..."
    return truncated + "..."


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
        document parts, limited to configured max_results with truncated text
        to stay within token limits. Returns empty list if search fails.
    """
    logger.debug("Starting semantic search for query length: %d characters", len(query))
    try:
        query_embedding = await ctx.deps.embeddings_service.generate_embedding(query)
        logger.debug("Generated embedding for search query")

        raw_results = cast(
            list[SearchResultSchema],
            await ctx.deps.embeddings_repository.search_similar(
                query_embedding=query_embedding,
                limit=ctx.deps.max_results,
            ),
        )

        results = []
        for result in raw_results:
            truncated_text = _truncate_text(
                result.document_part.text,
                ctx.deps.max_text_length,
            )
            truncated_result = SearchResultSchema(
                document_part=result.document_part.model_copy(
                    update={"text": truncated_text},
                ),
                score=result.score,
            )
            results.append(truncated_result)

        logger.debug(
            "Found parts for query: %s. First 100 chars from parts: %s",
            query,
            [
                result.document_part.text[:LOG_SHOW_CHARS_MAX] + "..."
                if len(result.document_part.text) > LOG_SHOW_CHARS_MAX
                else result.document_part.text
                for result in raw_results
            ],
        )
        logger.info(
            "Semantic search completed - found %d results with truncated content",
            len(results),
        )
    except Exception:
        logger.exception(
            "Failed to perform semantic search for query length: %d",
            len(query),
        )
        return []
    else:
        return results


def get_retrieval_agent(
    model: OpenAIModel,
    template_manager: TemplateManager,
    template_context: TemplateContextSchema | None = None,
) -> Agent[RetrievalDepsSchema, RetrievalResultSchema]:
    logger.debug("Creating retrieval agent")

    if template_context is None:
        template_context = TemplateContextSchema()  # type: ignore

    system_prompt = template_manager.render_template(
        "retrieval_system_prompt.j2",
        template_context,
    )

    agent = Agent(
        model=model,
        deps_type=RetrievalDepsSchema,
        output_type=RetrievalResultSchema,
        system_prompt=system_prompt,
        tools=[_semantic_search_tool],
    )

    logger.debug("Successfully created retrieval agent")
    return agent
