from qdrant_client import AsyncQdrantClient


class QdrantClient:
    def __init__(self, host: str, port: int) -> None:
        self._client = AsyncQdrantClient(host=host, grpc_port=port, prefer_grpc=True)
