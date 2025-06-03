from collections.abc import AsyncGenerator, Generator
from typing import TypedDict

import pytest
from minio import Minio
from qdrant_client import AsyncQdrantClient
from testcontainers.minio import MinioContainer
from testcontainers.qdrant import QdrantContainer


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
            port=container.get_exposed_port(9000),
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
            port=container.get_exposed_port(6334),
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
