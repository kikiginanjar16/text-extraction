from __future__ import annotations

from importlib import import_module
from pathlib import Path

from app.core.errors import ExtractionFailedError
from app.models import PageChunk


class PDFExtractor:
    def extract(self, path: Path, *, paginate_strategy: str = "auto") -> list[PageChunk]:
        _ = paginate_strategy
        try:
            fitz = import_module("fitz")
        except ModuleNotFoundError as exc:
            raise ExtractionFailedError("PDF extraction requires PyMuPDF to be installed") from exc

        try:
            document = fitz.open(path)
        except Exception as exc:
            raise ExtractionFailedError("File could not be parsed") from exc

        pages: list[PageChunk] = []
        for index in range(document.page_count):
            page = document.load_page(index)
            text = page.get_text("text").strip()
            pages.append(PageChunk(page=index + 1, text=text, page_kind="native"))
        document.close()
        return pages
