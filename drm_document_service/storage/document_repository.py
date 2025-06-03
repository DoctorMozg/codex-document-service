from uuid import UUID

from drm_document_service.schemas import DocumentSchema
from drm_document_service.storage.minio_client import MinioClient


class DocumentRepository:
    def __init__(self, minio_client: MinioClient) -> None:
        self._minio_client = minio_client

    async def save_document(self, document: DocumentSchema) -> str:
        if not document.name.lower().endswith(".pdf"):
            msg = "Document name must have .pdf extension"
            raise ValueError(msg)

        object_path = f"documents/{document.uid}/{document.name}"

        return await self._minio_client.upload_pdf_with_custom_path(
            document.body_bytes,
            object_path,
        )

    async def get_document(self, uid: UUID) -> DocumentSchema | None:
        documents = await self._list_documents_by_uid(uid)

        if not documents:
            return None

        document_name = documents[0]
        object_path = f"documents/{uid}/{document_name}"

        body_bytes = await self._minio_client.download_pdf(object_path)

        if body_bytes is None:
            return None

        return DocumentSchema(
            uid=uid,
            name=document_name,
            body_bytes=body_bytes,
        )

    async def _list_documents_by_uid(self, uid: UUID) -> list[str]:
        prefix = f"documents/{uid}/"
        object_names = await self._minio_client.list_objects_with_prefix(prefix)

        document_names = []
        for object_name in object_names:
            if object_name.startswith(prefix):
                document_name = object_name.split("/")[-1]
                if document_name.lower().endswith(".pdf"):
                    document_names.append(document_name)

        return document_names
