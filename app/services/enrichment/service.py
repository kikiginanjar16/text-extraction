from __future__ import annotations

from app.core.config import Settings
from app.models import EnrichmentResult, PageChunk

from .base import EnrichmentProvider, EnrichmentProviderError
from .fallback import fallback_enrichment, skipped_enrichment
from .openai_provider import OpenAIEnrichmentProvider


class EnrichmentService:
    def __init__(self, settings: Settings, provider: EnrichmentProvider | None = None) -> None:
        self.settings = settings
        self.provider = provider or OpenAIEnrichmentProvider(settings)

    def enrich(
        self,
        *,
        file_name: str,
        document_category: str,
        document_domain: str,
        baseline_tags: list[str],
        pages: list[PageChunk],
    ) -> EnrichmentResult:
        normalized_key = (self.settings.openai_api_key or "").strip()
        if not normalized_key:
            return skipped_enrichment(baseline_tags)

        try:
            return self.provider.enrich(
                api_key=normalized_key,
                file_name=file_name,
                document_category=document_category,
                document_domain=document_domain,
                baseline_tags=baseline_tags,
                pages=pages,
            )
        except EnrichmentProviderError:
            return fallback_enrichment(
                baseline_tags,
                provider="openai",
                model=self.settings.openai_model,
            )
