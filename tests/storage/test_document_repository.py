from uuid import uuid4

import pytest

from drm_document_service.schemas import DocumentSchema
from drm_document_service.storage.document_repository import DocumentRepository
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
def document_repository(minio_client: MinioClient) -> DocumentRepository:
    return DocumentRepository(minio_client)


@pytest.fixture
def sample_pdf_data() -> bytes:
    return (
        b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n"
        b">>\nendobj\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF"
    )


@pytest.fixture
def sample_document(sample_pdf_data: bytes) -> DocumentSchema:
    return DocumentSchema(
        uid=uuid4(),
        name="test_document.pdf",
        body_bytes=sample_pdf_data,
    )


@pytest.mark.asyncio
async def test_save_document_success(
    document_repository: DocumentRepository,
    sample_document: DocumentSchema,
) -> None:
    storage_path: str = await document_repository.save_document(sample_document)

    expected_path = (
        f"test-documents/documents/{sample_document.uid}/{sample_document.name}"
    )
    assert storage_path == expected_path


@pytest.mark.asyncio
async def test_save_document_non_pdf_raises_error(
    document_repository: DocumentRepository,
    sample_pdf_data: bytes,
) -> None:
    document = DocumentSchema(
        uid=uuid4(),
        name="not_a_pdf.txt",
        body_bytes=sample_pdf_data,
    )

    with pytest.raises(ValueError, match="Document name must have .pdf extension"):
        await document_repository.save_document(document)


@pytest.mark.asyncio
async def test_get_document_success(
    document_repository: DocumentRepository,
    sample_document: DocumentSchema,
) -> None:
    await document_repository.save_document(sample_document)

    retrieved_document: DocumentSchema | None = await document_repository.get_document(
        sample_document.uid,
    )

    assert retrieved_document is not None
    assert retrieved_document.uid == sample_document.uid
    assert retrieved_document.name == sample_document.name
    assert retrieved_document.body_bytes == sample_document.body_bytes


@pytest.mark.asyncio
async def test_get_document_nonexistent_returns_none(
    document_repository: DocumentRepository,
) -> None:
    nonexistent_uid = uuid4()

    retrieved_document: DocumentSchema | None = await document_repository.get_document(
        nonexistent_uid,
    )

    assert retrieved_document is None


@pytest.mark.asyncio
async def test_save_and_retrieve_multiple_documents(
    document_repository: DocumentRepository,
    sample_pdf_data: bytes,
) -> None:
    document1 = DocumentSchema(
        uid=uuid4(),
        name="document1.pdf",
        body_bytes=sample_pdf_data,
    )

    document2 = DocumentSchema(
        uid=uuid4(),
        name="document2.pdf",
        body_bytes=sample_pdf_data,
    )

    await document_repository.save_document(document1)
    await document_repository.save_document(document2)

    retrieved_doc1 = await document_repository.get_document(document1.uid)
    retrieved_doc2 = await document_repository.get_document(document2.uid)

    assert retrieved_doc1 is not None
    assert retrieved_doc2 is not None
    assert retrieved_doc1.uid == document1.uid
    assert retrieved_doc2.uid == document2.uid
