from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from drm_document_service.agents.pipeline import DocumentPipeline, get_pipeline
from drm_document_service.config import config
from drm_document_service.logic.embeddings_service import EmbeddingsService
from drm_document_service.logic.pdf_parser_service import PdfParserService
from drm_document_service.storage.document_repository import DocumentRepository
from drm_document_service.storage.embeddings_repository import EmbeddingsRepository
from drm_document_service.storage.minio_client import MinioClient
from drm_document_service.storage.qdrant_client import QdrantClient


@lru_cache
def get_minio_client() -> MinioClient:
    return MinioClient(
        host=config.minio_host,
        port=config.minio_port,
        access_key=config.minio_access_key,
        secret_key=config.minio_secret_key,
        bucket_name=config.minio_bucket_name,
    )


@lru_cache
def get_qdrant_client() -> QdrantClient:
    return QdrantClient(
        host=config.qdrant_host,
        port=config.qdrant_port,
    )


@lru_cache
def get_embeddings_service() -> EmbeddingsService:
    return EmbeddingsService(config=config)


@lru_cache
def get_pdf_parser_service() -> PdfParserService:
    return PdfParserService()


@lru_cache
def get_document_pipeline() -> DocumentPipeline:
    return get_pipeline(config)


def get_document_repository(
    minio_client: Annotated[MinioClient, Depends(get_minio_client)],
) -> DocumentRepository:
    return DocumentRepository(minio_client=minio_client)


def get_embeddings_repository(
    qdrant_client: Annotated[QdrantClient, Depends(get_qdrant_client)],
) -> EmbeddingsRepository:
    return EmbeddingsRepository(
        qdrant_client=qdrant_client,
        collection_name=config.qdrant_collection_name,
    )


MinioClientDep = Annotated[MinioClient, Depends(get_minio_client)]
QdrantClientDep = Annotated[QdrantClient, Depends(get_qdrant_client)]
DocumentRepositoryDep = Annotated[DocumentRepository, Depends(get_document_repository)]
EmbeddingsRepositoryDep = Annotated[
    EmbeddingsRepository,
    Depends(get_embeddings_repository),
]
EmbeddingsServiceDep = Annotated[EmbeddingsService, Depends(get_embeddings_service)]
PdfParserServiceDep = Annotated[PdfParserService, Depends(get_pdf_parser_service)]
DocumentPipelineDep = Annotated[DocumentPipeline, Depends(get_document_pipeline)]
