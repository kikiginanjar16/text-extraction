from __future__ import annotations

from importlib import import_module
from pathlib import Path

from app.core.config import Settings
from app.core.errors import ExtractionFailedError
from app.models import PageChunk

from .text_virtual import paginate_text


class DocxExtractor:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def extract(self, path: Path, *, paginate_strategy: str = "auto") -> list[PageChunk]:
        _ = paginate_strategy
        try:
            docx = import_module("docx")
        except ModuleNotFoundError as exc:
            raise ExtractionFailedError("DOCX extraction requires python-docx to be installed") from exc

        try:
            document = docx.Document(path)
        except Exception as exc:
            raise ExtractionFailedError("File could not be parsed") from exc

        parts: list[str] = []
        parts.extend(paragraph.text for paragraph in document.paragraphs)
        for table in document.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    parts.append(row_text)

        return paginate_text(
            "\n".join(parts),
            max_lines_per_page=self.settings.virtual_max_lines_per_page,
            max_chars_per_page=self.settings.virtual_max_chars_per_page,
            page_kind="virtual",
        )


class PptxExtractor:
    def extract(self, path: Path, *, paginate_strategy: str = "auto") -> list[PageChunk]:
        _ = paginate_strategy
        try:
            pptx = import_module("pptx")
        except ModuleNotFoundError as exc:
            raise ExtractionFailedError("PPTX extraction requires python-pptx to be installed") from exc

        try:
            presentation = pptx.Presentation(path)
        except Exception as exc:
            raise ExtractionFailedError("File could not be parsed") from exc

        pages: list[PageChunk] = []
        for index, slide in enumerate(presentation.slides, start=1):
            snippets: list[str] = []
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text:
                    snippets.append(shape.text.strip())
            pages.append(
                PageChunk(
                    page=index,
                    text="\n".join(part for part in snippets if part).strip(),
                    page_kind="rendered",
                )
            )
        return pages


class XlsExtractor:
    def extract(self, path: Path, *, paginate_strategy: str = "auto") -> list[PageChunk]:
        _ = paginate_strategy
        try:
            xlrd = import_module("xlrd")
        except ModuleNotFoundError as exc:
            raise ExtractionFailedError("XLS extraction requires xlrd to be installed") from exc

        try:
            workbook = xlrd.open_workbook(path)
        except Exception as exc:
            raise ExtractionFailedError("File could not be parsed") from exc

        pages: list[PageChunk] = []
        for index in range(workbook.nsheets):
            sheet = workbook.sheet_by_index(index)
            rows: list[str] = []
            for row_index in range(sheet.nrows):
                values = [str(value).strip() for value in sheet.row_values(row_index)]
                row_text = "\t".join(value for value in values if value)
                if row_text:
                    rows.append(row_text)
            pages.append(
                PageChunk(
                    page=index + 1,
                    text="\n".join(rows).strip(),
                    page_kind="rendered",
                )
            )
        return pages
