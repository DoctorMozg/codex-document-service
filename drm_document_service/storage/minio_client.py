import asyncio
import logging
from io import BytesIO
from typing import cast

from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)

PDF_CONTENT_TYPE = "application/pdf"


class MinioClient:
    def __init__(
        self,
        host: str,
        port: int,
        access_key: str,
        secret_key: str,
        bucket_name: str = "documents",
    ) -> None:
        logger.info(
            "Initializing MinioClient with host: %s, port: %d, bucket: %s",
            host,
            port,
            bucket_name,
        )
        self._client = Minio(
            endpoint=f"{host}:{port}",
            access_key=access_key,
            secret_key=secret_key,
            secure=False,
        )
        self.bucket_name = bucket_name

    async def _ensure_bucket_exists(self) -> None:
        logger.debug("Ensuring bucket exists: %s", self.bucket_name)
        await asyncio.to_thread(self._create_bucket_if_not_exists)
        logger.debug("Bucket check completed: %s", self.bucket_name)

    def _create_bucket_if_not_exists(self) -> None:
        if not self._client.bucket_exists(self.bucket_name):
            logger.info("Creating bucket: %s", self.bucket_name)
            self._client.make_bucket(self.bucket_name)
            logger.info("Successfully created bucket: %s", self.bucket_name)
        else:
            logger.debug("Bucket already exists: %s", self.bucket_name)

    async def upload_pdf_with_custom_path(
        self,
        file_data: bytes,
        object_path: str,
    ) -> str:
        logger.debug(
            "Uploading PDF to path: %s, size: %d bytes",
            object_path,
            len(file_data),
        )
        await self._ensure_bucket_exists()

        file_stream = BytesIO(file_data)

        await asyncio.to_thread(
            self._client.put_object,
            self.bucket_name,
            object_path,
            file_stream,
            length=len(file_data),
            content_type=PDF_CONTENT_TYPE,
        )

        result = f"{self.bucket_name}/{object_path}"
        logger.info("Successfully uploaded PDF to: %s", result)
        return result

    async def download_pdf(self, object_path: str) -> bytes | None:
        logger.debug("Downloading PDF from path: %s", object_path)
        try:
            response = await asyncio.to_thread(
                self._client.get_object,
                self.bucket_name,
                object_path,
            )
            result = cast(bytes, response.read())
            logger.debug(
                "Successfully downloaded PDF from: %s, size: %d bytes",
                object_path,
                len(result),
            )
        except S3Error:
            logger.warning("PDF not found at path: %s", object_path)
            return None
        else:
            return result
        finally:
            if "response" in locals():
                response.close()

    async def list_objects_with_prefix(self, prefix: str) -> list[str]:
        logger.debug("Listing objects with prefix: %s", prefix)
        try:
            objects = await asyncio.to_thread(
                self._client.list_objects,
                self.bucket_name,
                prefix=prefix,
                recursive=True,
            )

            object_names = [obj.object_name for obj in objects]
            logger.debug("Found %d objects with prefix: %s", len(object_names), prefix)
        except S3Error:
            logger.warning("Failed to list objects with prefix: %s", prefix)
            return []
        else:
            return object_names

    async def delete_object(self, object_path: str) -> bool:
        logger.debug("Deleting object at path: %s", object_path)
        try:
            await asyncio.to_thread(
                self._client.remove_object,
                self.bucket_name,
                object_path,
            )
            logger.info("Successfully deleted object: %s", object_path)
        except S3Error:
            logger.warning("Failed to delete object: %s", object_path)
            return False
        else:
            return True
