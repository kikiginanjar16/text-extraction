from __future__ import annotations

from app.core.config import Settings
from app.core.errors import UnsupportedFileTypeError

from .strategies.office_legacy import LegacyOfficeExtractor
from .strategies.office_modern import DocxExtractor, PptxExtractor, XlsExtractor
from .strategies.pdf import PDFExtractor
from .strategies.text_virtual import TextVirtualExtractor


class ExtractionResolver:
    def __init__(self, settings: Settings) -> None:
        pdf_extractor = PDFExtractor()
        self._strategies = {
            "pdf": pdf_extractor,
            "md": TextVirtualExtractor(settings),
            "txt": TextVirtualExtractor(settings),
            "docx": DocxExtractor(settings),
            "pptx": PptxExtractor(),
            "xls": XlsExtractor(),
            "doc": LegacyOfficeExtractor(pdf_extractor),
            "ppt": LegacyOfficeExtractor(pdf_extractor),
        }

    def resolve(self, file_type: str):
        try:
            return self._strategies[file_type]
        except KeyError as exc:
            raise UnsupportedFileTypeError(
                "Supported file types: pdf, docx, pptx, md, txt, doc, ppt, xls"
            ) from exc
