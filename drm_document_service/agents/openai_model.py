import logging

from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from drm_document_service.config import AppConfigSchema

logger = logging.getLogger(__name__)


def get_base_model(config: AppConfigSchema) -> OpenAIModel:
    logger.debug("Creating OpenAI model: %s", config.openai_model)
    model = OpenAIModel(
        config.openai_model,
        provider=OpenAIProvider(api_key=config.openai_api_key),
    )
    logger.debug("Successfully created OpenAI model: %s", config.openai_model)
    return model
