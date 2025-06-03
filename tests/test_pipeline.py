from unittest.mock import AsyncMock

import pytest

from drm_document_service.agents.pipeline import DocumentPipeline
from drm_document_service.config import AppConfigSchema
from drm_document_service.schemas import OrchestratorResultSchema


@pytest.fixture
def mock_config() -> AppConfigSchema:
    return AppConfigSchema(
        openai_api_key="test-key",
        minio_access_key="test-access",
        minio_secret_key="test-secret",
    )


@pytest.fixture
def pipeline(mock_config: AppConfigSchema) -> DocumentPipeline:
    return DocumentPipeline(mock_config)


@pytest.mark.asyncio
async def test_pipeline_initialization(pipeline: DocumentPipeline) -> None:
    assert pipeline.orchestrator_agent is not None
    assert pipeline.guardrail_agent is not None
    assert pipeline.retrieval_agent is not None
    assert pipeline.embeddings_service is not None
    assert pipeline.embeddings_repository is not None


@pytest.mark.asyncio
async def test_process_query_error_handling(pipeline: DocumentPipeline) -> None:
    pipeline.orchestrator_agent.run = AsyncMock(side_effect=Exception("Test error"))

    result = await pipeline.process_query("test query")

    assert isinstance(result, OrchestratorResultSchema)
    assert result.query == "test query"
    assert result.is_relevant is False
    assert result.confidence == 0.0
    assert "error processing" in result.answer.lower()


@pytest.mark.asyncio
async def test_health_check_success(pipeline: DocumentPipeline) -> None:
    pipeline.embeddings_repository.ensure_collection_exists = AsyncMock()

    result = await pipeline.health_check()

    assert result is True


@pytest.mark.asyncio
async def test_health_check_failure(pipeline: DocumentPipeline) -> None:
    pipeline.embeddings_repository.ensure_collection_exists = AsyncMock(
        side_effect=Exception("Connection failed"),
    )

    result = await pipeline.health_check()

    assert result is False
