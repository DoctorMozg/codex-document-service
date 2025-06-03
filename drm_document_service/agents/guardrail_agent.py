import logging
from dataclasses import dataclass

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

from drm_document_service.agents.template_manager import (
    TemplateContextSchema,
    TemplateManager,
)
from drm_document_service.schemas import GuardrailResultSchema

logger = logging.getLogger(__name__)


@dataclass
class GuardrailDepsSchema:
    pass


def get_guardrail_agent(
    model: OpenAIModel,
    template_manager: TemplateManager,
    template_context: TemplateContextSchema | None = None,
) -> Agent[GuardrailDepsSchema, GuardrailResultSchema]:
    if template_context is None:
        template_context = TemplateContextSchema()

    system_prompt = template_manager.render_template(
        "guardrail_system_prompt.j2",
        template_context,
    )

    return Agent(
        model=model,
        deps_type=GuardrailDepsSchema,
        output_type=GuardrailResultSchema,
        system_prompt=system_prompt,
    )
