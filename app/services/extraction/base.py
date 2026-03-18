from __future__ import annotations

from pathlib import Path
from typing import Protocol

from app.models import PageChunk


class ExtractorStrategy(Protocol):
    def extract(self, path: Path, *, paginate_strategy: str = "auto") -> list[PageChunk]:
        ...
