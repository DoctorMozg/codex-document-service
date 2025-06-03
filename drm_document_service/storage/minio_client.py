import asyncio
from io import BytesIO
from typing import cast

from minio import Minio
from minio.error import S3Error

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
        self._client = Minio(
            endpoint=f"{host}:{port}",
            access_key=access_key,
            secret_key=secret_key,
            secure=False,
        )
        self.bucket_name = bucket_name

    async def _ensure_bucket_exists(self) -> None:
        await asyncio.to_thread(self._create_bucket_if_not_exists)

    def _create_bucket_if_not_exists(self) -> None:
        if not self._client.bucket_exists(self.bucket_name):
            self._client.make_bucket(self.bucket_name)

    async def upload_pdf_with_custom_path(
        self,
        file_data: bytes,
        object_path: str,
    ) -> str:
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

        return f"{self.bucket_name}/{object_path}"

    async def download_pdf(self, object_path: str) -> bytes | None:
        try:
            response = await asyncio.to_thread(
                self._client.get_object,
                self.bucket_name,
                object_path,
            )
            return cast(bytes, response.read())
        except S3Error:
            return None
        finally:
            if "response" in locals():
                response.close()

    async def list_objects_with_prefix(self, prefix: str) -> list[str]:
        try:
            objects = await asyncio.to_thread(
                self._client.list_objects,
                self.bucket_name,
                prefix=prefix,
                recursive=True,
            )

            object_names = [obj.object_name for obj in objects]
        except S3Error:
            return []
        else:
            return object_names
