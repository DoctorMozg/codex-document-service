from unittest.mock import Mock
from uuid import uuid4

import pytest

from drm_document_service.logic.pdf_parser_service import PdfParserService
from drm_document_service.schemas import DocumentSchema


@pytest.fixture
def pdf_parser_service():
    return PdfParserService()


def test_split_text_into_chunks_single_paragraph(pdf_parser_service):
    text = (
        "This is a single paragraph with multiple sentences. "
        "It contains several words and should remain as one chunk."
    )
    chunks = pdf_parser_service._split_text_into_chunks(text, max_document_text_length=1000)

    assert len(chunks) == 1
    assert chunks[0] == text


def test_split_text_into_chunks_multiple_paragraphs(pdf_parser_service):
    text = (
        "First paragraph with some content.\n\n"
        "Second paragraph with different content.\n\n"
        "Third paragraph here."
    )
    chunks = pdf_parser_service._split_text_into_chunks(text, max_document_text_length=1000)

    assert len(chunks) == 3
    assert chunks[0] == "First paragraph with some content."
    assert chunks[1] == "Second paragraph with different content."
    assert chunks[2] == "Third paragraph here."


def test_split_text_into_chunks_empty_text(pdf_parser_service):
    chunks = pdf_parser_service._split_text_into_chunks("", max_document_text_length=1000)
    assert chunks == []


def test_split_text_into_chunks_whitespace_only(pdf_parser_service):
    chunks = pdf_parser_service._split_text_into_chunks("   \n\n  ", max_document_text_length=1000)
    assert chunks == []


def test_split_text_into_chunks_paragraphs_with_extra_spacing(
    pdf_parser_service,
):
    text = (
        "First paragraph.\n\n\n\n"
        "Second paragraph with extra spacing.\n\n   \n\n"
        "Third paragraph."
    )
    chunks = pdf_parser_service._split_text_into_chunks(text, max_document_text_length=1000)

    assert len(chunks) == 3
    assert chunks[0] == "First paragraph."
    assert chunks[1] == "Second paragraph with extra spacing."
    assert chunks[2] == "Third paragraph."


def test_parse_document(pdf_parser_service):
    document = DocumentSchema(
        uid=uuid4(),
        name="test.pdf",
        body_bytes=b"mock pdf content",
    )

    with pytest.MonkeyPatch().context() as m:
        m.setattr(
            pdf_parser_service,
            "_extract_text_from_pdf",
            Mock(return_value="First paragraph.\n\nSecond paragraph."),
        )

        result = pdf_parser_service.parse_document(document, max_document_text_length=1000)

        assert len(result) == 2
        assert result[0].document_uid == document.uid
        assert result[0].text == "First paragraph."
        assert result[1].document_uid == document.uid
        assert result[1].text == "Second paragraph."
        assert hasattr(result[0], "uid")
        assert hasattr(result[1], "uid")
        assert not hasattr(result[0], "embedding")
        assert not hasattr(result[1], "embedding")
