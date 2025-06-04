from uuid import UUID


class DocumentServiceError(Exception):
    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DocumentNotFoundError(DocumentServiceError):
    def __init__(self, document_uid: UUID) -> None:
        super().__init__(f"Document with ID {document_uid} not found", 404)


class InvalidFileTypeError(DocumentServiceError):
    def __init__(self, filename: str) -> None:
        super().__init__(
            f"Invalid file type. Only PDF files are allowed: {filename}",
            400,
        )


class FileTooLargeError(DocumentServiceError):
    def __init__(self, size_mb: float, max_size_mb: int) -> None:
        super().__init__(
            f"File too large ({size_mb:.1f}MB). Maximum size: {max_size_mb}MB",
            413,
        )


class DocumentProcessingError(DocumentServiceError):
    def __init__(self, message: str) -> None:
        super().__init__(f"Document processing failed: {message}", 500)


class QueryProcessingError(DocumentServiceError):
    def __init__(self, message: str) -> None:
        super().__init__(f"Query processing failed: {message}", 500)
