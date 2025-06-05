import logging
from typing import cast

from drm_document_service.agents.guardrail_agent import (
    GuardrailDepsSchema,
    get_guardrail_agent,
)
from drm_document_service.agents.openai_model import get_base_model
from drm_document_service.agents.orchestrator_agent import (
    OrchestratorDepsSchema,
    get_orchestrator_agent,
)
from drm_document_service.agents.retrieval_agent import (
    RetrievalDepsSchema,
    get_retrieval_agent,
)
from drm_document_service.agents.template_manager import get_template_manager
from drm_document_service.config import AppConfigSchema
from drm_document_service.logic.embeddings_service import EmbeddingsService
from drm_document_service.schemas import OrchestratorResultSchema
from drm_document_service.storage.embeddings_repository import EmbeddingsRepository
from drm_document_service.storage.qdrant_client import QdrantClient

logger = logging.getLogger(__name__)


class DocumentPipeline:
    def __init__(self, config: AppConfigSchema) -> None:
        logger.info("Initializing DocumentPipeline")
        self.config = config
        self._initialize_dependencies()
        self._initialize_agents()
        logger.info("DocumentPipeline initialization completed")

    def _initialize_dependencies(self) -> None:
        logger.debug("Initializing dependencies")
        self.model = get_base_model(self.config)
        self.template_manager = get_template_manager()
        self.embeddings_service = EmbeddingsService(self.config)

        qdrant_client = QdrantClient(self.config.qdrant_host, self.config.qdrant_port)
        self.embeddings_repository = EmbeddingsRepository(
            qdrant_client,
            self.config.qdrant_collection_name,
        )
        logger.debug("Successfully initialized all dependencies")

    def _initialize_agents(self) -> None:
        logger.debug("Initializing agents")
        self.guardrail_agent = get_guardrail_agent(self.model, self.template_manager)
        self.retrieval_agent = get_retrieval_agent(self.model, self.template_manager)

        self.guardrail_deps = GuardrailDepsSchema()
        self.retrieval_deps = RetrievalDepsSchema(
            embeddings_service=self.embeddings_service,
            embeddings_repository=self.embeddings_repository,
            max_results=self.config.max_retrieval_results,
            max_text_length=self.config.max_document_text_length,
        )

        orchestrator_deps = OrchestratorDepsSchema(
            guardrail_agent=self.guardrail_agent,
            retrieval_agent=self.retrieval_agent,
            guardrail_deps=self.guardrail_deps,
            retrieval_deps=self.retrieval_deps,
        )

        self.orchestrator_agent = get_orchestrator_agent(
            self.model,
            self.template_manager,
        )
        self.orchestrator_deps = orchestrator_deps
        logger.debug("Successfully initialized all agents")

    async def process_query(self, query: str) -> OrchestratorResultSchema:
        logger.info("Processing query with length: %d characters", len(query))
        try:
            result = await self.orchestrator_agent.run(
                query,
                deps=self.orchestrator_deps,
            )
            orchestrator_result = cast(OrchestratorResultSchema, result.output)
            logger.info(
                "Query processing completed - relevant: %s,"
                " confidence: %.2f, sources: %d",
                orchestrator_result.is_relevant,
                orchestrator_result.confidence,
                len(orchestrator_result.sources),
            )
        except Exception:
            logger.exception("Failed to process query with length: %d", len(query))
            return OrchestratorResultSchema(
                answer="I apologize, but I encountered an error processing your query.",
                sources=[],
                is_relevant=False,
                confidence=0.0,
                query=query,
            )
        else:
            return orchestrator_result


def get_pipeline(config: AppConfigSchema | None = None) -> DocumentPipeline:
    logger.debug("Creating DocumentPipeline instance")
    if config is None:
        from drm_document_service.config import config as default_config

        config = default_config

    pipeline = DocumentPipeline(config)
    logger.debug("Successfully created DocumentPipeline instance")
    return pipeline
