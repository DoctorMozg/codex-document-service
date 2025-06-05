from collections.abc import AsyncGenerator, Generator
from typing import TypedDict
from uuid import UUID, uuid4

import pytest
from minio import Minio
from qdrant_client import AsyncQdrantClient
from testcontainers.minio import MinioContainer
from testcontainers.qdrant import QdrantContainer

from drm_document_service.config import AppConfigSchema
from drm_document_service.schemas import (
    DocumentInfoSchema,
    DocumentPartSchema,
    DocumentSchema,
    EmbeddedDocumentPartSchema,
)


class MinioConfig(TypedDict):
    host: str
    port: int
    access_key: str
    secret_key: str


class QdrantConfig(TypedDict):
    host: str
    port: int
    url: str


class TestServices(TypedDict):
    minio: MinioConfig
    qdrant: QdrantConfig


@pytest.fixture(scope="session")
def minio_container() -> Generator[MinioConfig]:
    with (
        MinioContainer("minio/minio:latest")
        .with_exposed_ports(9000)
        .with_env("MINIO_ACCESS_KEY", "drm-document-service")
        .with_env("MINIO_SECRET_KEY", "drm-document-service-secret-key")
        .with_command("server /data") as container
    ):
        yield MinioConfig(
            host=container.get_container_host_ip(),
            port=int(container.get_exposed_port(9000)),
            access_key="drm-document-service",
            secret_key="drm-document-service-secret-key",  # noqa: S106
        )


@pytest.fixture(scope="session")
def qdrant_container() -> Generator[QdrantConfig]:
    with QdrantContainer("qdrant/qdrant:latest").with_exposed_ports(
        6333,
        6334,
    ) as container:
        yield QdrantConfig(
            host=container.get_container_host_ip(),
            port=int(container.get_exposed_port(6334)),
            url=f"http://{container.get_container_host_ip()}:{container.get_exposed_port(6334)}",
        )


@pytest.fixture(scope="session")
def test_services(
    minio_container: MinioConfig,
    qdrant_container: QdrantConfig,
) -> TestServices:
    return TestServices(
        minio=minio_container,
        qdrant=qdrant_container,
    )


@pytest.fixture(autouse=True)
def cleanup_minio(minio_container: MinioConfig) -> Generator[None]:
    yield

    client = Minio(
        endpoint=f"{minio_container['host']}:{minio_container['port']}",
        access_key=minio_container["access_key"],
        secret_key=minio_container["secret_key"],
        secure=False,
    )

    try:
        buckets = client.list_buckets()
        for bucket in buckets:
            objects = client.list_objects(bucket.name, recursive=True)
            for obj in objects:
                client.remove_object(bucket.name, obj.object_name)
    except Exception:  # noqa: S110, BLE001
        pass


@pytest.fixture(autouse=True)
async def cleanup_qdrant(qdrant_container: QdrantConfig) -> AsyncGenerator[None]:
    yield

    client = AsyncQdrantClient(
        host=qdrant_container["host"],
        grpc_port=qdrant_container["port"],
        prefer_grpc=True,
    )

    try:
        collections = await client.get_collections()
        for collection in collections.collections:
            await client.delete_collection(collection.name)
        await client.close()
    except Exception:  # noqa: S110, BLE001
        pass


@pytest.fixture
def sample_document_uid() -> UUID:
    return uuid4()


@pytest.fixture
def sample_pdf_content() -> bytes:
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj"


@pytest.fixture
def sample_document_schema(
    sample_document_uid: UUID,
    sample_pdf_content: bytes,
) -> DocumentSchema:
    return DocumentSchema(
        uid=sample_document_uid,
        name="test_document.pdf",
        body_bytes=sample_pdf_content,
    )


@pytest.fixture
def sample_document_info(sample_document_uid: UUID) -> DocumentInfoSchema:
    return DocumentInfoSchema(
        uid=sample_document_uid,
        name="test_document.pdf",
        upload_date="2024-01-01T12:00:00",
        size_bytes=1024,
    )


@pytest.fixture
def sample_document_part(sample_document_uid: UUID) -> DocumentPartSchema:
    return DocumentPartSchema(
        uid=uuid4(),
        document_uid=sample_document_uid,
        text="This is a sample document part content.",
    )


@pytest.fixture
def sample_embedded_part(
    sample_document_part: DocumentPartSchema,
) -> EmbeddedDocumentPartSchema:
    return EmbeddedDocumentPartSchema(
        uid=sample_document_part.uid,
        document_uid=sample_document_part.document_uid,
        text=sample_document_part.text,
        embedding=[0.1] * 1536,
    )


@pytest.fixture
def mock_config() -> AppConfigSchema:
    return AppConfigSchema(
        OPEN_AI_KEY="test-key",
    )
