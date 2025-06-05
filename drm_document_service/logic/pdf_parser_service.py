import io
import logging
import re
from uuid import uuid4

from pypdf import PdfReader

from drm_document_service.schemas import DocumentPartSchema, DocumentSchema

logger = logging.getLogger(__name__)


class PdfParserService:
    def parse_document(self, document: DocumentSchema) -> list[DocumentPartSchema]:
        logger.info(
            "Parsing PDF document: %s (size: %d bytes)",
            document.name,
            len(document.body_bytes),
        )
        text = self._extract_text_from_pdf(document.body_bytes)
        chunks = self._split_text_into_chunks(text)

        parts = [
            DocumentPartSchema(
                uid=uuid4(),
                document_uid=document.uid,
                text=chunk,
            )
            for chunk in chunks
        ]

        logger.info(
            "Successfully parsed PDF document: %s into %d parts",
            document.name,
            len(parts),
        )
        return parts

    def _extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        logger.debug("Extracting text from PDF (size: %d bytes)", len(pdf_bytes))
        try:
            pdf_stream = io.BytesIO(pdf_bytes)
            reader = PdfReader(pdf_stream)

            text_parts = [page.extract_text() for page in reader.pages]
            text = "\n\n".join(text_parts)

            logger.debug(
                "Successfully extracted %d characters from %d pages",
                len(text),
                len(reader.pages),
            )
        except Exception:
            logger.exception(
                "Failed to extract text from PDF (size: %d bytes)",
                len(pdf_bytes),
            )
            raise
        else:
            return text

    def _split_text_into_chunks(self, text: str) -> list[str]:
        logger.debug(
            "Splitting text into chunks (text length: %d characters)",
            len(text),
        )
        paragraphs = re.split(r"\n\s*\n", text.strip())
        chunks = [paragraph.strip() for paragraph in paragraphs if paragraph.strip()]

        logger.debug("Successfully split text into %d chunks", len(chunks))
        return chunks
