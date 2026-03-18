from __future__ import annotations

from app.models import EnrichmentMetadata, EnrichmentResult


def skipped_enrichment(tags: list[str]) -> EnrichmentResult:
    return EnrichmentResult(
        summary=None,
        tags=tags,
        enrichment=EnrichmentMetadata(
            status="skipped",
            ai_used=False,
            provider=None,
            model=None,
        ),
    )


def fallback_enrichment(tags: list[str], *, provider: str | None, model: str | None) -> EnrichmentResult:
    return EnrichmentResult(
        summary=None,
        tags=tags,
        enrichment=EnrichmentMetadata(
            status="fallback",
            ai_used=False,
            provider=provider,
            model=model,
        ),
    )
