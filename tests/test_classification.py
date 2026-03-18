import unittest

from app.models import PageChunk
from app.services.classification.service import ClassificationService


class ClassificationServiceTest(unittest.TestCase):
    def test_detects_finance_report(self) -> None:
        service = ClassificationService()
        result = service.classify(
            file_name="q2_finance_report.txt",
            pages=[
                PageChunk(
                    page=1,
                    text="Quarterly financial report with revenue, budget, and cash flow analysis.",
                    page_kind="virtual",
                )
            ],
        )

        self.assertEqual(result.document_category, "report")
        self.assertEqual(result.document_domain, "finance")
        self.assertIn("report", result.tags)
        self.assertIn("finance", result.tags)


if __name__ == "__main__":
    unittest.main()
