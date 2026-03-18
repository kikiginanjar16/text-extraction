import unittest

from app.core.config import Settings
from app.models import EnrichmentMetadata, EnrichmentResult, PageChunk
from app.services.enrichment.base import EnrichmentProviderError
from app.services.enrichment.service import EnrichmentService


class FakeProvider:
    def enrich(self, **_: object) -> EnrichmentResult:
        return EnrichmentResult(
            summary="Ringkasan singkat dokumen.",
            tags=["finance", "budget"],
            enrichment=EnrichmentMetadata(
                status="applied",
                ai_used=True,
                provider="openai",
                model="test-model",
            ),
        )


class FailingProvider:
    def enrich(self, **_: object) -> EnrichmentResult:
        raise EnrichmentProviderError("provider failed")


class EnrichmentServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = Settings(
            max_file_size_mb=50,
            virtual_max_lines_per_page=50,
            virtual_max_chars_per_page=3500,
            remote_fetch_timeout_sec=20,
            openai_api_key=None,
            swagger_username=None,
            swagger_password=None,
            openai_api_base="https://api.openai.com/v1",
            openai_model="gpt-4.1-mini",
            openai_timeout_sec=20,
            openai_excerpt_chars=8000,
        )
        self.pages = [PageChunk(page=1, text="Budget and forecast overview", page_kind="virtual")]

    def test_skips_ai_when_key_missing(self) -> None:
        service = EnrichmentService(self.settings, provider=FakeProvider())
        result = service.enrich(
            file_name="budget.txt",
            document_category="report",
            document_domain="finance",
            baseline_tags=["report", "finance"],
            pages=self.pages,
        )
        self.assertEqual(result.enrichment.status, "skipped")
        self.assertIsNone(result.summary)
        self.assertEqual(result.tags, ["report", "finance"])

    def test_falls_back_when_provider_fails(self) -> None:
        service = EnrichmentService(
            Settings(
                max_file_size_mb=50,
                virtual_max_lines_per_page=50,
                virtual_max_chars_per_page=3500,
                remote_fetch_timeout_sec=20,
                openai_api_key="sk-test",
                swagger_username=None,
                swagger_password=None,
                openai_api_base="https://api.openai.com/v1",
                openai_model="gpt-4.1-mini",
                openai_timeout_sec=20,
                openai_excerpt_chars=8000,
            ),
            provider=FailingProvider(),
        )
        result = service.enrich(
            file_name="budget.txt",
            document_category="report",
            document_domain="finance",
            baseline_tags=["report", "finance"],
            pages=self.pages,
        )
        self.assertEqual(result.enrichment.status, "fallback")
        self.assertFalse(result.enrichment.ai_used)
        self.assertEqual(result.tags, ["report", "finance"])

    def test_applies_ai_when_provider_succeeds(self) -> None:
        service = EnrichmentService(
            Settings(
                max_file_size_mb=50,
                virtual_max_lines_per_page=50,
                virtual_max_chars_per_page=3500,
                remote_fetch_timeout_sec=20,
                openai_api_key="sk-test",
                swagger_username=None,
                swagger_password=None,
                openai_api_base="https://api.openai.com/v1",
                openai_model="gpt-4.1-mini",
                openai_timeout_sec=20,
                openai_excerpt_chars=8000,
            ),
            provider=FakeProvider(),
        )
        result = service.enrich(
            file_name="budget.txt",
            document_category="report",
            document_domain="finance",
            baseline_tags=["report", "finance"],
            pages=self.pages,
        )
        self.assertEqual(result.enrichment.status, "applied")
        self.assertTrue(result.enrichment.ai_used)
        self.assertEqual(result.summary, "Ringkasan singkat dokumen.")


if __name__ == "__main__":
    unittest.main()
