from fastapi import APIRouter

from drm_document_service.deps import DocumentPipelineDep
from drm_document_service.exceptions import QueryProcessingError
from drm_document_service.schemas import QueryRequestSchema, QueryResponseSchema

router = APIRouter()


@router.post("/query")
async def query_documents(
    request: QueryRequestSchema,
    pipeline: DocumentPipelineDep,
) -> QueryResponseSchema:
    try:
        result = await pipeline.process_query(request.question)

        return QueryResponseSchema(
            answer=result.answer,
            sources=result.sources,
            is_relevant=result.is_relevant,
            confidence=result.confidence,
            query=result.query,
        )
    except Exception as e:
        raise QueryProcessingError(str(e)) from e
