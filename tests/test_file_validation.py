import asyncio
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.errors import FileTooLargeError, InvalidRequestError, UnsupportedFileTypeError
from app.main import app
from app.services.extraction.service import ExtractionService
from app.services.storage.temp_files import cleanup_persisted_upload, persist_upload


class FakeUpload:
    def __init__(self, filename: str, chunks: list[bytes]) -> None:
        self.filename = filename
        self._chunks = list(chunks)

    async def read(self, size: int = -1) -> bytes:
        _ = size
        if not self._chunks:
            return b""
        return self._chunks.pop(0)


class UploadValidationApiTest(unittest.TestCase):
    @patch("app.api.routes.extract.temporary_upload")
    def test_rejects_upload_when_content_type_mismatches_extension(self, temporary_upload) -> None:
        client = TestClient(app)

        response = client.post(
            "/v1/extract",
            files={"file": ("report.pdf", b"plain text payload", "text/plain")},
        )

        self.assertEqual(response.status_code, 415)
        self.assertEqual(response.json()["error"]["code"], "UNSUPPORTED_FILE_TYPE")
        temporary_upload.assert_not_called()

    def test_removes_temp_upload_after_processing_error(self) -> None:
        client = TestClient(app, raise_server_exceptions=False)
        captured_paths: list[Path] = []
        original_cleanup = cleanup_persisted_upload

        def tracked_cleanup(persisted) -> None:
            captured_paths.append(persisted.path)
            original_cleanup(persisted)

        with (
            patch("app.api.routes.extract._build_response", side_effect=InvalidRequestError("boom")),
            patch("app.services.storage.temp_files.cleanup_persisted_upload", side_effect=tracked_cleanup),
        ):
            response = client.post(
                "/v1/extract",
                files={"file": ("notes.txt", b"hello", "text/plain")},
            )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(len(captured_paths), 1)
        self.assertFalse(captured_paths[0].exists())


class PersistUploadLifecycleTest(unittest.TestCase):
    def test_persist_upload_uses_temp_dir_and_cleanup_removes_it(self) -> None:
        persisted = asyncio.run(
            persist_upload(
                FakeUpload("notes.txt", [b"hello world"]),
                max_size_bytes=1024,
            )
        )

        self.assertTrue(persisted.path.exists())
        self.assertTrue(persisted.temp_dir.exists())
        self.assertEqual(persisted.temp_dir, persisted.path.parent)
        self.assertTrue(str(persisted.temp_dir).startswith(tempfile.gettempdir()))

        cleanup_persisted_upload(persisted)

        self.assertFalse(persisted.temp_dir.exists())
        self.assertFalse(persisted.path.exists())

    def test_persist_upload_cleans_temp_dir_when_size_limit_exceeded(self) -> None:
        forced_temp_dir = Path(tempfile.mkdtemp(prefix="text-extraction-test-"))

        with patch("app.services.storage.temp_files.mkdtemp", return_value=str(forced_temp_dir)):
            with self.assertRaises(FileTooLargeError):
                asyncio.run(
                    persist_upload(
                        FakeUpload("notes.txt", [b"12345", b"67890"]),
                        max_size_bytes=8,
                    )
                )

        self.assertFalse(forced_temp_dir.exists())


class ExtractionServiceValidationTest(unittest.TestCase):
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

    def test_allows_generic_declared_content_type(self) -> None:
        service = ExtractionService(self.settings)

        service.validate_upload(
            original_name="report.pdf",
            declared_mime_type="application/octet-stream",
        )

    @patch.object(ExtractionService, "_detect_mime_type", return_value="text/plain")
    def test_rejects_detected_mime_type_mismatch(self, _: object) -> None:
        service = ExtractionService(self.settings)

        with self.assertRaises(UnsupportedFileTypeError):
            service.extract(
                Path("report.pdf"),
                original_name="report.pdf",
                include_empty_pages=True,
                paginate_strategy="auto",
            )


if __name__ == "__main__":
    unittest.main()
