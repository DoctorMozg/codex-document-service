from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfigSchema(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    log_level: str = Field(default="DEBUG", alias="LOG_LEVEL")

    service_host: str = Field(default="127.0.0.1", alias="SERVICE_HOST")
    service_port: int = Field(default=8000, alias="SERVICE_PORT")

    minio_host: str = Field(default="minio", alias="MINIO_HOST")
    minio_port: int = Field(default=9000, alias="MINIO_PORT")
    minio_access_key: str = Field(alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(alias="MINIO_SECRET_KEY")
    minio_bucket_name: str = Field(default="documents")
    minio_secure: bool = Field(default=False)

    qdrant_host: str = Field(default="qdrant", alias="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, alias="QDRANT_PORT")
    qdrant_collection_name: str = Field(default="documents")

    openai_api_key: str = Field(alias="OPEN_AI_KEY")
    openai_model: str = Field(default="gpt-4o")
    openai_embedding_model: str = Field(default="text-embedding-3-small")

    max_file_size_mb: int = Field(default=10)

    @property
    def minio_endpoint(self) -> str:
        protocol = "https" if self.minio_secure else "http"
        return f"{protocol}://{self.minio_host}:{self.minio_port}"


config = AppConfigSchema()
