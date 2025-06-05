from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field

Embeddings = Annotated[list[float], Field(min_length=1536, max_length=1536)]


class DocumentPartSchema(BaseModel):
    uid: UUID
    document_uid: UUID
    text: str


class EmbeddedDocumentPartSchema(DocumentPartSchema):
    embedding: Embeddings


class DocumentSchema(BaseModel):
    uid: UUID
    name: str
    body_bytes: bytes


class DocumentInfoSchema(BaseModel):
    uid: UUID
    name: str
    upload_date: str
    size_bytes: int


class SearchResultSchema(BaseModel):
    document_part: DocumentPartSchema
    score: float


class RetrievalResultSchema(BaseModel):
    results: list[SearchResultSchema]
    query: str
    total_results: int


class GuardrailResultSchema(BaseModel):
    is_allowed: bool
    reason: str
    confidence: float


class SourceSchema(BaseModel):
    document_name: str
    document_uid: UUID
    part_uid: UUID
    text_snippet: str
    relevance_score: float


class OrchestratorResultSchema(BaseModel):
    answer: str
    sources: list[SourceSchema]
    is_relevant: bool
    confidence: float
    query: str


class QueryRequestSchema(BaseModel):
    question: Annotated[str, Field(min_length=1)]


class QueryResponseSchema(BaseModel):
    answer: str
    sources: list[SourceSchema]
    is_relevant: bool
    confidence: float
    query: str


class UploadResponseSchema(BaseModel):
    document_uid: UUID
    filename: str
    message: str


class DocumentListSchema(BaseModel):
    documents: list[DocumentInfoSchema]
    total_count: int


class DeleteResponseSchema(BaseModel):
    message: str
    document_uid: UUID
