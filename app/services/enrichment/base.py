from __future__ import annotations

from typing import Protocol

from app.models import EnrichmentResult, PageChunk


class EnrichmentProviderError(Exception):
    """Raised when the optional AI provider cannot produce a usable result."""


class EnrichmentProvider(Protocol):
    def enrich(
        self,
        *,
        api_key: str,
        file_name: str,
        document_category: str,
        document_domain: str,
        baseline_tags: list[str],
        pages: list[PageChunk],
    ) -> EnrichmentResult:
        ...
