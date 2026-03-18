from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class PageChunk:
    page: int
    text: str
    page_kind: str

    @property
    def char_count(self) -> int:
        return len(self.text)

    @property
    def is_empty(self) -> bool:
        return not self.text.strip()

    def as_dict(self) -> dict[str, Any]:
        return {
            "page": self.page,
            "text": self.text,
            "char_count": self.char_count,
            "is_empty": self.is_empty,
            "page_kind": self.page_kind,
        }


@dataclass(slots=True)
class ClassificationMetadata:
    confidence: float
    method: str
    model: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "confidence": round(self.confidence, 4),
            "method": self.method,
            "model": self.model,
        }


@dataclass(slots=True)
class ClassificationResult:
    document_category: str
    document_domain: str
    tags: list[str]
    classification: ClassificationMetadata


@dataclass(slots=True)
class EnrichmentMetadata:
    status: str
    ai_used: bool
    provider: str | None
    model: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "ai_used": self.ai_used,
            "provider": self.provider,
            "model": self.model,
        }


@dataclass(slots=True)
class EnrichmentResult:
    summary: str | None
    tags: list[str]
    enrichment: EnrichmentMetadata


@dataclass(slots=True)
class ExtractedFile:
    file_name: str
    file_type: str
    mime_type: str
    pages: list[PageChunk]


@dataclass(slots=True)
class ExtractResponsePayload:
    file_name: str
    file_type: str
    mime_type: str
    document_category: str
    document_domain: str
    summary: str | None
    tags: list[str]
    classification: ClassificationMetadata
    enrichment: EnrichmentMetadata
    pages: list[PageChunk]

    @property
    def page_count(self) -> int:
        return len(self.pages)

    def as_dict(self) -> dict[str, Any]:
        return {
            "file_name": self.file_name,
            "file_type": self.file_type,
            "mime_type": self.mime_type,
            "document_category": self.document_category,
            "document_domain": self.document_domain,
            "summary": self.summary,
            "tags": self.tags,
            "classification": self.classification.as_dict(),
            "enrichment": self.enrichment.as_dict(),
            "page_count": self.page_count,
            "pages": [page.as_dict() for page in self.pages],
        }
