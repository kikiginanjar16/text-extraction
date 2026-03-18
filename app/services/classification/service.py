from __future__ import annotations

from app.models import ClassificationResult, PageChunk

from .rules import classify_document


class ClassificationService:
    def classify(self, *, file_name: str, pages: list[PageChunk]) -> ClassificationResult:
        return classify_document(file_name, pages)
