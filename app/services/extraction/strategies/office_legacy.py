from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from app.core.errors import ExtractionFailedError
from app.models import PageChunk

from .pdf import PDFExtractor


class LegacyOfficeExtractor:
    def __init__(self, pdf_extractor: PDFExtractor) -> None:
        self.pdf_extractor = pdf_extractor

    def extract(self, path: Path, *, paginate_strategy: str = "auto") -> list[PageChunk]:
        _ = paginate_strategy
        converter = shutil.which("soffice") or shutil.which("libreoffice")
        if not converter:
            raise ExtractionFailedError("Legacy Office conversion requires LibreOffice or soffice")

        with tempfile.TemporaryDirectory() as tmp_dir:
            result = subprocess.run(
                [
                    converter,
                    "--headless",
                    "--convert-to",
                    "pdf",
                    str(path),
                    "--outdir",
                    tmp_dir,
                ],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            if result.returncode != 0:
                raise ExtractionFailedError("File could not be parsed")

            converted = Path(tmp_dir) / f"{path.stem}.pdf"
            if not converted.exists():
                raise ExtractionFailedError("Legacy conversion did not produce a PDF output")

            return self.pdf_extractor.extract(converted)
