import unittest

from app.services.extraction.strategies.text_virtual import paginate_text


class TextVirtualPaginationTest(unittest.TestCase):
    def test_uses_form_feed_as_page_break(self) -> None:
        pages = paginate_text(
            "Alpha\fBeta",
            max_lines_per_page=50,
            max_chars_per_page=3500,
        )
        self.assertEqual(len(pages), 2)
        self.assertEqual(pages[0].text, "Alpha")
        self.assertEqual(pages[1].text, "Beta")

    def test_splits_long_text_deterministically(self) -> None:
        text = "\n".join(f"line-{index}" for index in range(120))
        pages = paginate_text(
            text,
            max_lines_per_page=50,
            max_chars_per_page=10_000,
        )
        self.assertEqual(len(pages), 3)
        self.assertEqual(pages[0].page, 1)
        self.assertEqual(pages[-1].page, 3)


if __name__ == "__main__":
    unittest.main()
