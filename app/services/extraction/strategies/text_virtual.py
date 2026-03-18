from __future__ import annotations

from pathlib import Path

from app.core.config import Settings
from app.core.errors import ExtractionFailedError
from app.models import PageChunk


def read_text_file(path: Path) -> str:
    encodings = ("utf-8", "utf-16", "latin-1")
    for encoding in encodings:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
        except OSError as exc:
            raise ExtractionFailedError(f"Failed to read text file: {exc}") from exc
    raise ExtractionFailedError("File could not be decoded as text")


def paginate_text(
    text: str,
    *,
    max_lines_per_page: int,
    max_chars_per_page: int,
    page_kind: str = "virtual",
) -> list[PageChunk]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if "\f" in normalized:
        parts = normalized.split("\f")
        return [
            PageChunk(page=index, text=part.strip(), page_kind=page_kind)
            for index, part in enumerate(parts, start=1)
        ]

    lines = normalized.split("\n")
    buffer: list[str] = []
    pages: list[PageChunk] = []
    current_chars = 0

    def flush() -> None:
        if not buffer and pages:
            return
        page_text = "\n".join(buffer).strip()
        pages.append(PageChunk(page=len(pages) + 1, text=page_text, page_kind=page_kind))
        buffer.clear()

    for line in lines:
        projected_chars = current_chars + len(line) + (1 if buffer else 0)
        if buffer and (len(buffer) >= max_lines_per_page or projected_chars > max_chars_per_page):
            flush()
            current_chars = 0
        buffer.append(line)
        current_chars += len(line) + (1 if buffer else 0)

    if buffer or not pages:
        flush()

    return pages


class TextVirtualExtractor:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def extract(self, path: Path, *, paginate_strategy: str = "auto") -> list[PageChunk]:
        _ = paginate_strategy
        text = read_text_file(path)
        return paginate_text(
            text,
            max_lines_per_page=self.settings.virtual_max_lines_per_page,
            max_chars_per_page=self.settings.virtual_max_chars_per_page,
            page_kind="virtual",
        )
