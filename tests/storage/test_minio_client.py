from pathlib import Path

import pytest

from drm_document_service.storage.minio_client import MinioClient
from tests.conftest import MinioConfig


@pytest.fixture
def minio_client(minio_container: MinioConfig) -> MinioClient:
    return MinioClient(
        host=minio_container["host"],
        port=minio_container["port"],
        access_key=minio_container["access_key"],
        secret_key=minio_container["secret_key"],
        bucket_name="test-documents",
    )


@pytest.fixture
def sample_pdf_file(tmp_path: Path) -> Path:
    pdf_file: Path = tmp_path / "sample.pdf"
    pdf_file.write_bytes(
        b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\n"
        b"endobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF",
    )
    return pdf_file


@pytest.fixture
def sample_pdf_data() -> bytes:
    return (
        b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n"
        b">>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF"
    )


def test_initialization(minio_container: MinioConfig) -> None:
    client: MinioClient = MinioClient(
        host=minio_container["host"],
        port=minio_container["port"],
        access_key=minio_container["access_key"],
        secret_key=minio_container["secret_key"],
    )

    assert client.bucket_name == "documents"


def test_initialization_with_custom_bucket(
    minio_container: MinioConfig,
) -> None:
    custom_bucket: str = "custom-bucket"
    client: MinioClient = MinioClient(
        host=minio_container["host"],
        port=minio_container["port"],
        access_key=minio_container["access_key"],
        secret_key=minio_container["secret_key"],
        bucket_name=custom_bucket,
    )

    assert client.bucket_name == custom_bucket


@pytest.mark.asyncio
async def test_ensure_bucket_exists_creates_bucket(
    minio_client: MinioClient,
) -> None:
    await minio_client._ensure_bucket_exists()

    bucket_exists: bool = minio_client._client.bucket_exists(
        minio_client.bucket_name,
    )
    assert bucket_exists


@pytest.mark.asyncio
async def test_upload_pdf_with_custom_path_success(
    minio_client: MinioClient,
    sample_pdf_data: bytes,
) -> None:
    object_path: str = "documents/test-uuid/test_document.pdf"
    object_key: str = await minio_client.upload_pdf_with_custom_path(
        sample_pdf_data,
        object_path,
    )

    assert object_key == f"{minio_client.bucket_name}/{object_path}"

    bucket_exists: bool = minio_client._client.bucket_exists(
        minio_client.bucket_name,
    )
    assert bucket_exists


@pytest.mark.asyncio
async def test_download_pdf_success(
    minio_client: MinioClient,
    sample_pdf_data: bytes,
) -> None:
    object_path: str = "documents/test-uuid/test_document.pdf"

    await minio_client.upload_pdf_with_custom_path(sample_pdf_data, object_path)

    downloaded_data: bytes | None = await minio_client.download_pdf(object_path)

    assert downloaded_data is not None
    assert downloaded_data == sample_pdf_data


@pytest.mark.asyncio
async def test_download_pdf_nonexistent_file_returns_none(
    minio_client: MinioClient,
) -> None:
    object_path: str = "documents/nonexistent/file.pdf"

    downloaded_data: bytes | None = await minio_client.download_pdf(object_path)

    assert downloaded_data is None


@pytest.mark.asyncio
async def test_list_objects_with_prefix_success(
    minio_client: MinioClient,
    sample_pdf_data: bytes,
) -> None:
    prefix = "documents/test-uuid/"
    object_path1 = f"{prefix}document1.pdf"
    object_path2 = f"{prefix}document2.pdf"

    await minio_client.upload_pdf_with_custom_path(sample_pdf_data, object_path1)
    await minio_client.upload_pdf_with_custom_path(sample_pdf_data, object_path2)

    object_names = await minio_client.list_objects_with_prefix(prefix)

    assert len(object_names) == 2
    assert object_path1 in object_names
    assert object_path2 in object_names


@pytest.mark.asyncio
async def test_list_objects_with_prefix_empty_result(
    minio_client: MinioClient,
) -> None:
    prefix = "documents/nonexistent-uuid/"

    object_names = await minio_client.list_objects_with_prefix(prefix)

    assert object_names == []
