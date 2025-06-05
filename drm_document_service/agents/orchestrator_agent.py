import logging
from dataclasses import dataclass
from typing import cast

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel

from drm_document_service.agents.guardrail_agent import GuardrailDepsSchema
from drm_document_service.agents.retrieval_agent import RetrievalDepsSchema
from drm_document_service.agents.template_manager import (
    TemplateContextSchema,
    TemplateManager,
)
from drm_document_service.schemas import (
    GuardrailResultSchema,
    OrchestratorResultSchema,
    RetrievalResultSchema,
)

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorDepsSchema:
    guardrail_agent: Agent[GuardrailDepsSchema, GuardrailResultSchema]
    guardrail_deps: GuardrailDepsSchema

    retrieval_agent: Agent[RetrievalDepsSchema, RetrievalResultSchema]
    retrieval_deps: RetrievalDepsSchema


async def _check_query_safety(
    ctx: RunContext[OrchestratorDepsSchema],
    query: str,
) -> GuardrailResultSchema:
    """Check if a query is safe and appropriate for processing.
    
    This tool should be called AFTER document retrieval to validate the query
    along with the retrieved results for comprehensive safety assessment.
    
    Args:
        query: The user query to validate for safety and appropriateness
    
    Returns:
        Safety assessment including whether query is allowed and confidence score
    """
    logger.debug("Checking query safety for query length: %d characters", len(query))
    try:
        result = await ctx.deps.guardrail_agent.run(query, deps=ctx.deps.guardrail_deps)
        guardrail_result = cast(GuardrailResultSchema, result.output)
        logger.info(
            "Query safety check completed - allowed: %s, confidence: %.2f",
            guardrail_result.is_allowed,
            guardrail_result.confidence,
        )
    except Exception:
        logger.exception(
            "Failed to check query safety for query length: %d",
            len(query),
        )
        return GuardrailResultSchema(
            is_allowed=False,
            reason="Safety check failed",
            confidence=0.0,
        )
    else:
        return guardrail_result


async def _retrieve_documents(
    ctx: RunContext[OrchestratorDepsSchema],
    query: str,
) -> RetrievalResultSchema:
    """Retrieve relevant documents based on the user query.
    
    This tool should be called FIRST to gather relevant documents.
    The results should then be used with the safety check tool for validation.
    
    Args:
        query: The user query to find relevant documents for
    
    Returns:
        Retrieved documents with relevance scores and metadata
    """
    logger.debug(
        "Starting document retrieval for query length: %d characters",
        len(query),
    )
    try:
        result = await ctx.deps.retrieval_agent.run(query, deps=ctx.deps.retrieval_deps)
        retrieval_result = cast(RetrievalResultSchema, result.output)
        logger.info(
            "Document retrieval completed - found %d results",
            retrieval_result.total_results,
        )
    except Exception:
        logger.exception(
            "Failed to retrieve documents for query length: %d",
            len(query),
        )
        return RetrievalResultSchema(results=[], query=query, total_results=0)
    else:
        return retrieval_result


def get_orchestrator_agent(
    model: OpenAIModel,
    template_manager: TemplateManager,
    template_context: TemplateContextSchema | None = None,
) -> Agent[OrchestratorDepsSchema, OrchestratorResultSchema]:
    logger.debug("Creating orchestrator agent")

    if template_context is None:
        template_context = TemplateContextSchema()  # type: ignore

    system_prompt = template_manager.render_template(
        "orchestrator_system_prompt.j2",
        template_context,
    )

    agent = Agent(
        model=model,
        deps_type=OrchestratorDepsSchema,
        output_type=OrchestratorResultSchema,
        system_prompt=system_prompt,
        tools=[_check_query_safety, _retrieve_documents],
    )

    logger.debug("Successfully created orchestrator agent")
    return agent
