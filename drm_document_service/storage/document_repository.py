import logging
from datetime import UTC, datetime
from uuid import UUID

from drm_document_service.schemas import DocumentInfoSchema, DocumentSchema
from drm_document_service.storage.minio_client import MinioClient

logger = logging.getLogger(__name__)

DOCUMENT_PATH_PARTS = 3


class DocumentRepository:
    def __init__(self, minio_client: MinioClient) -> None:
        logger.debug("Initializing DocumentRepository")
        self._minio_client = minio_client

    async def save_document(self, document: DocumentSchema) -> str:
        logger.info("Saving document: %s with UID: %s", document.name, document.uid)

        if not document.name.lower().endswith(".pdf"):
            logger.error("Invalid document extension for: %s", document.name)
            msg = "Document name must have .pdf extension"
            raise ValueError(msg)

        object_path = f"documents/{document.uid}/{document.name}"

        result = await self._minio_client.upload_pdf_with_custom_path(
            document.body_bytes,
            object_path,
        )
        logger.info(
            "Successfully saved document: %s at path: %s",
            document.name,
            object_path,
        )
        return result

    async def get_document(self, uid: UUID) -> DocumentSchema | None:
        logger.debug("Getting document with UID: %s", uid)

        documents = await self._list_documents_by_uid(uid)

        if not documents:
            logger.debug("No documents found for UID: %s", uid)
            return None

        document_name = documents[0]
        object_path = f"documents/{uid}/{document_name}"

        body_bytes = await self._minio_client.download_pdf(object_path)

        if body_bytes is None:
            logger.warning(
                "Document bytes not found for UID: %s at path: %s",
                uid,
                object_path,
            )
            return None

        logger.debug(
            "Successfully retrieved document: %s for UID: %s",
            document_name,
            uid,
        )
        return DocumentSchema(
            uid=uid,
            name=document_name,
            body_bytes=body_bytes,
        )

    async def list_documents(self) -> list[DocumentInfoSchema]:
        logger.debug("Listing all documents")

        all_objects = await self._minio_client.list_objects_with_prefix("documents/")

        documents = []
        for object_name in all_objects:
            if object_name.endswith(".pdf"):
                parts = object_name.split("/")
                if len(parts) >= DOCUMENT_PATH_PARTS:
                    uid_str = parts[1]
                    filename = parts[2]

                    try:
                        uid = UUID(uid_str)
                        documents.append(
                            DocumentInfoSchema(
                                uid=uid,
                                name=filename,
                                upload_date=datetime.now(UTC).isoformat(),
                                size_bytes=0,
                            ),
                        )
                    except ValueError:
                        logger.warning("Invalid UUID in object path: %s", object_name)
                        continue

        logger.info("Successfully listed %d documents", len(documents))
        return documents

    async def get_document_info(self, uid: UUID) -> DocumentInfoSchema | None:
        logger.debug("Getting document info for UID: %s", uid)

        documents = await self._list_documents_by_uid(uid)

        if not documents:
            logger.debug("No document info found for UID: %s", uid)
            return None

        document_name = documents[0]

        logger.debug("Successfully retrieved document info for UID: %s", uid)
        return DocumentInfoSchema(
            uid=uid,
            name=document_name,
            upload_date=datetime.now(UTC).isoformat(),
            size_bytes=0,
        )

    async def delete_document(self, uid: UUID) -> bool:
        logger.info("Deleting document with UID: %s", uid)

        documents = await self._list_documents_by_uid(uid)

        if not documents:
            logger.debug("No documents found to delete for UID: %s", uid)
            return False

        for document_name in documents:
            object_path = f"documents/{uid}/{document_name}"
            await self._minio_client.delete_object(object_path)

        logger.info(
            "Successfully deleted %d documents for UID: %s",
            len(documents),
            uid,
        )
        return True

    async def _list_documents_by_uid(self, uid: UUID) -> list[str]:
        logger.debug("Listing documents by UID: %s", uid)

        prefix = f"documents/{uid}/"
        object_names = await self._minio_client.list_objects_with_prefix(prefix)

        document_names = []
        for object_name in object_names:
            if object_name.startswith(prefix):
                document_name = object_name.split("/")[-1]
                if document_name.lower().endswith(".pdf"):
                    document_names.append(document_name)

        logger.debug("Found %d documents for UID: %s", len(document_names), uid)
        return document_names
