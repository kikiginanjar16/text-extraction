from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, Body, File, Form, UploadFile
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.models import ExtractResponsePayload
from app.schemas.request import normalize_paginate_strategy
from app.schemas.response import serialize_extract_response
from app.services.classification.service import ClassificationService
from app.services.enrichment.service import EnrichmentService
from app.services.extraction.service import ExtractionService
from app.services.storage.temp_files import cleanup_file, download_remote_file, persist_upload

router = APIRouter(tags=["extract"])

settings = get_settings()
extraction_service = ExtractionService(settings)
classification_service = ClassificationService()
enrichment_service = EnrichmentService(settings)


def _build_response(
    *,
    original_name: str,
    persisted_path: Path,
    include_empty_pages: bool,
    paginate_strategy: str,
) -> JSONResponse:
    extracted = extraction_service.extract(
        persisted_path,
        original_name=original_name,
        include_empty_pages=include_empty_pages,
        paginate_strategy=paginate_strategy,
    )
    classified = classification_service.classify(
        file_name=extracted.file_name,
        pages=extracted.pages,
    )
    enriched = enrichment_service.enrich(
        file_name=extracted.file_name,
        document_category=classified.document_category,
        document_domain=classified.document_domain,
        baseline_tags=classified.tags,
        pages=extracted.pages,
    )
    payload = ExtractResponsePayload(
        file_name=extracted.file_name,
        file_type=extracted.file_type,
        mime_type=extracted.mime_type,
        document_category=classified.document_category,
        document_domain=classified.document_domain,
        summary=enriched.summary,
        tags=enriched.tags,
        classification=classified.classification,
        enrichment=enriched.enrichment,
        pages=extracted.pages,
    )
    return JSONResponse(content=serialize_extract_response(payload))


@router.post("/v1/extract")
async def extract_text(
    file: UploadFile = File(...),
    include_empty_pages: bool = Form(default=True),
    paginate_strategy: str = Form(default="auto"),
) -> JSONResponse:
    normalized_strategy = normalize_paginate_strategy(paginate_strategy)
    persisted = await persist_upload(file, max_size_bytes=settings.max_file_size_bytes)
    try:
        return _build_response(
            original_name=persisted.original_name,
            persisted_path=persisted.path,
            include_empty_pages=include_empty_pages,
            paginate_strategy=normalized_strategy,
        )
    finally:
        cleanup_file(persisted.path)


@router.post("/v1/extract-url")
async def extract_text_from_url(
    url: str = Body(...),
    include_empty_pages: bool = Body(default=True),
    paginate_strategy: str = Body(default="auto"),
) -> JSONResponse:
    normalized_strategy = normalize_paginate_strategy(paginate_strategy)
    persisted = await asyncio.to_thread(
        download_remote_file,
        url,
        max_size_bytes=settings.max_file_size_bytes,
        timeout_sec=settings.remote_fetch_timeout_sec,
    )
    try:
        return _build_response(
            original_name=persisted.original_name,
            persisted_path=persisted.path,
            include_empty_pages=include_empty_pages,
            paginate_strategy=normalized_strategy,
        )
    finally:
        cleanup_file(persisted.path)
