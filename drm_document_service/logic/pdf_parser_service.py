import io
import logging
import re
from uuid import uuid4

from pypdf import PdfReader

from drm_document_service.schemas import DocumentPartSchema, DocumentSchema

logger = logging.getLogger(__name__)


class PdfParserService:
    def parse_document(self, document: DocumentSchema) -> list[DocumentPartSchema]:
        text = self._extract_text_from_pdf(document.body_bytes)
        chunks = self._split_text_into_chunks(text)

        return [
            DocumentPartSchema(
                uid=uuid4(),
                document_uid=document.uid,
                text=chunk,
            )
            for chunk in chunks
        ]

    def _extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        try:
            pdf_stream = io.BytesIO(pdf_bytes)
            reader = PdfReader(pdf_stream)

            text_parts = [page.extract_text() for page in reader.pages]

            return "\n\n".join(text_parts)
        except Exception:
            logger.exception("Failed to extract text from PDF")
            raise

    def _split_text_into_chunks(self, text: str) -> list[str]:
        paragraphs = re.split(r"\n\s*\n", text.strip())

        return [paragraph.strip() for paragraph in paragraphs if paragraph.strip()]
