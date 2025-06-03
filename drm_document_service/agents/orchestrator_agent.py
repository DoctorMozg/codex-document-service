import logging
from dataclasses import dataclass

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
    retrieval_agent: Agent[RetrievalDepsSchema, RetrievalResultSchema]
    guardrail_deps: GuardrailDepsSchema
    retrieval_deps: RetrievalDepsSchema


async def _check_query_safety(
    ctx: RunContext[OrchestratorDepsSchema],
    query: str,
) -> GuardrailResultSchema:
    try:
        result = await ctx.deps.guardrail_agent.run(query, deps=ctx.deps.guardrail_deps)
        return result.output
    except Exception:
        logger.exception("Failed to check query safety")
        return GuardrailResultSchema(
            is_allowed=False,
            reason="Safety check failed",
            confidence=0.0,
        )


async def _retrieve_documents(
    ctx: RunContext[OrchestratorDepsSchema],
    query: str,
) -> RetrievalResultSchema:
    try:
        result = await ctx.deps.retrieval_agent.run(query, deps=ctx.deps.retrieval_deps)
        return result.output
    except Exception:
        logger.exception("Failed to retrieve documents")
        return RetrievalResultSchema(results=[], query=query, total_results=0)


def get_orchestrator_agent(
    model: OpenAIModel,
    template_manager: TemplateManager,
    template_context: TemplateContextSchema | None = None,
) -> Agent[OrchestratorDepsSchema, OrchestratorResultSchema]:
    if template_context is None:
        template_context = TemplateContextSchema()

    system_prompt = template_manager.render_template(
        "orchestrator_system_prompt.j2",
        template_context,
    )

    return Agent(
        model=model,
        deps_type=OrchestratorDepsSchema,
        output_type=OrchestratorResultSchema,
        system_prompt=system_prompt,
        tools=[_check_query_safety, _retrieve_documents],
    )
