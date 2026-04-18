from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import Response

from drm_document_service.deps import DocumentRepositoryDep
from drm_document_service.exceptions import DocumentNotFoundError
from drm_document_service.schemas import (
    DeleteResponseSchema,
    DocumentInfoSchema,
    DocumentListSchema,
)

router = APIRouter()


@router.get("/documents")
async def list_documents(
    document_repo: DocumentRepositoryDep,
) -> DocumentListSchema:
    """List all indexed documents with basic metadata."""
    documents = await document_repo.list_documents()

    document_infos = [
        DocumentInfoSchema(
            uid=doc.uid,
            name=doc.name,
            upload_date=doc.upload_date,
            size_bytes=doc.size_bytes,
        )
        for doc in documents
    ]

    return DocumentListSchema(
        documents=document_infos,
        total_count=len(document_infos),
    )


@router.get("/documents/{document_uid}/info")
async def get_document_info(
    document_uid: UUID,
    document_repo: DocumentRepositoryDep,
) -> DocumentInfoSchema:
    """Return metadata for a single document by its UID."""
    document_info = await document_repo.get_document_info(document_uid)

    if not document_info:
        raise DocumentNotFoundError(document_uid)

    return DocumentInfoSchema(
        uid=document_info.uid,
        name=document_info.name,
        upload_date=document_info.upload_date,
        size_bytes=document_info.size_bytes,
    )


@router.get("/documents/{document_uid}/download")
async def download_document(
    document_uid: UUID,
    document_repo: DocumentRepositoryDep,
) -> Response:
    """Download the original PDF for a given document UID."""
    document = await document_repo.get_document(document_uid)

    if not document:
        raise DocumentNotFoundError(document_uid)

    return Response(
        content=document.body_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={document.name}"},
    )


@router.delete("/documents/{document_uid}")
async def delete_document(
    document_uid: UUID,
    document_repo: DocumentRepositoryDep,
) -> DeleteResponseSchema:
    """Remove a document and its associated embeddings from storage."""
    deleted = await document_repo.delete_document(document_uid)

    if not deleted:
        raise DocumentNotFoundError(document_uid)

    return DeleteResponseSchema(
        message="Document deleted successfully",
        document_uid=document_uid,
    )
