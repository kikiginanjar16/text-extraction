from __future__ import annotations


class ServiceError(Exception):
    def __init__(self, message: str, *, code: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class InvalidRequestError(ServiceError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="INVALID_REQUEST", status_code=422)


class UnsupportedFileTypeError(ServiceError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="UNSUPPORTED_FILE_TYPE", status_code=415)


class FileTooLargeError(ServiceError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="FILE_TOO_LARGE", status_code=413)


class ExtractionFailedError(ServiceError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="EXTRACTION_FAILED", status_code=422)
