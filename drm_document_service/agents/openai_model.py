from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider

from drm_document_service.config import AppConfigSchema


def get_base_model(config: AppConfigSchema) -> OpenAIModel:
    return OpenAIModel(
        config.openai_model,
        provider=OpenAIProvider(api_key=config.openai_api_key),
    )
