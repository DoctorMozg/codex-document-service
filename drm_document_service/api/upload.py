from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, File, UploadFile

from drm_document_service.config import config
from drm_document_service.deps import (
    DocumentRepositoryDep,
    EmbeddingsRepositoryDep,
    EmbeddingsServiceDep,
    PdfParserServiceDep,
)
from drm_document_service.exceptions import (
    DocumentProcessingError,
    FileTooLargeError,
    InvalidFileTypeError,
)
from drm_document_service.schemas import DocumentSchema, UploadResponseSchema

router = APIRouter()


@router.post("/upload")
async def upload_pdf(
    document_repo: DocumentRepositoryDep,
    embeddings_repo: EmbeddingsRepositoryDep,
    embeddings_service: EmbeddingsServiceDep,
    pdf_parser: PdfParserServiceDep,
    file: Annotated[UploadFile, File()] = ...,
) -> UploadResponseSchema:
    """Upload a PDF, parse it into chunks, and index embeddings for retrieval."""
    if not file.filename or not file.filename.endswith(".pdf"):
        raise InvalidFileTypeError(file.filename or "unknown")

    file_content = await file.read()
    file_size_mb = len(file_content) / (1024 * 1024)

    if file_size_mb > config.max_file_size_mb:
        raise FileTooLargeError(file_size_mb, config.max_file_size_mb)

    try:
        document_uid = uuid4()

        document = DocumentSchema(
            uid=document_uid,
            name=file.filename,
            body_bytes=file_content,
        )

        await document_repo.save_document(document)

        document_parts = pdf_parser.parse_document(
            document,
            config.max_document_text_length,
        )

        embedded_parts = await embeddings_service.embed_document_parts(document_parts)

        await embeddings_repo.store_embeddings(embedded_parts)

        return UploadResponseSchema(
            document_uid=document_uid,
            filename=file.filename,
            message=f"Successfully uploaded and processed {len(document_parts)} parts",
        )
    except Exception as e:
        raise DocumentProcessingError(str(e)) from e
