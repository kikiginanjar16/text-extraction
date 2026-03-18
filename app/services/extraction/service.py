from __future__ import annotations

import mimetypes
from importlib import import_module
from pathlib import Path

from app.core.config import Settings
from app.core.errors import ExtractionFailedError, InvalidRequestError, UnsupportedFileTypeError
from app.models import ExtractedFile, PageChunk

from .resolver import ExtractionResolver

SUPPORTED_FILE_TYPES = {"pdf", "docx", "pptx", "md", "txt", "doc", "ppt", "xls"}
SUPPORTED_MIME_TYPES = {
    "pdf": {"application/pdf", "application/x-pdf"},
    "docx": {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
    },
    "pptx": {
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/zip",
    },
    "md": {"text/markdown", "text/x-markdown", "text/plain"},
    "txt": {"text/plain"},
    "doc": {
        "application/msword",
        "application/vnd.ms-word",
        "application/x-ole-storage",
        "application/vnd.ms-office",
        "application/cdfv2",
    },
    "ppt": {
        "application/vnd.ms-powerpoint",
        "application/x-ole-storage",
        "application/vnd.ms-office",
        "application/cdfv2",
    },
    "xls": {
        "application/vnd.ms-excel",
        "application/x-ole-storage",
        "application/vnd.ms-office",
        "application/cdfv2",
    },
}
GENERIC_MIME_TYPES = {"application/octet-stream", "binary/octet-stream"}


def _normalize_mime_type(mime_type: str | None) -> str | None:
    if not mime_type:
        return None
    normalized = mime_type.split(";", 1)[0].strip().lower()
    return normalized or None


class ExtractionService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.resolver = ExtractionResolver(settings)

    def validate_upload(self, *, original_name: str | None, declared_mime_type: str | None = None) -> None:
        file_type = self._detect_file_type(original_name or "")
        self._validate_mime_type(file_type, declared_mime_type)

    def extract(
        self,
        path: Path,
        *,
        original_name: str,
        declared_mime_type: str | None = None,
        include_empty_pages: bool,
        paginate_strategy: str,
    ) -> ExtractedFile:
        file_type = self._detect_file_type(original_name)
        self._validate_mime_type(file_type, declared_mime_type)
        mime_type = self._detect_mime_type(path, original_name)
        self._validate_mime_type(file_type, mime_type)
        extractor = self.resolver.resolve(file_type)
        pages = extractor.extract(path, paginate_strategy=paginate_strategy)
        pages = self._normalize_pages(pages, include_empty_pages=include_empty_pages)
        return ExtractedFile(
            file_name=Path(original_name).name,
            file_type=file_type,
            mime_type=mime_type,
            pages=pages,
        )

    def _detect_file_type(self, original_name: str) -> str:
        suffix = Path(original_name).suffix.lower().lstrip(".")
        if not suffix:
            raise InvalidRequestError("Uploaded file must have an extension")
        if suffix not in SUPPORTED_FILE_TYPES:
            raise UnsupportedFileTypeError(
                "Supported file types: pdf, docx, pptx, md, txt, doc, ppt, xls"
            )
        return suffix

    def _detect_mime_type(self, path: Path, original_name: str) -> str:
        try:
            magic = import_module("magic")
        except (ImportError, ModuleNotFoundError):
            guessed, _ = mimetypes.guess_type(original_name)
            return guessed or "application/octet-stream"

        try:
            detected = magic.from_file(str(path), mime=True)
        except Exception:
            guessed, _ = mimetypes.guess_type(original_name)
            return guessed or "application/octet-stream"
        return detected or "application/octet-stream"

    def _validate_mime_type(self, file_type: str, mime_type: str | None) -> None:
        normalized = _normalize_mime_type(mime_type)
        if normalized is None or normalized in GENERIC_MIME_TYPES:
            return

        allowed = SUPPORTED_MIME_TYPES[file_type]
        if normalized not in allowed:
            raise UnsupportedFileTypeError("File MIME type does not match extension")

    def _normalize_pages(self, pages: list[PageChunk], *, include_empty_pages: bool) -> list[PageChunk]:
        normalized = pages
        if not include_empty_pages:
            normalized = [page for page in pages if not page.is_empty]
        if not normalized:
            normalized = [PageChunk(page=1, text="", page_kind="virtual")]
        return [
            PageChunk(page=index, text=page.text, page_kind=page.page_kind)
            for index, page in enumerate(normalized, start=1)
        ]
