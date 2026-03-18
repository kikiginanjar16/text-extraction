from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes.extract import router as extract_router
from app.core.errors import ServiceError
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(
    title="Text Extraction API",
    version="0.1.0",
    summary="Extract text from supported document types into an ordered pages array.",
)
app.include_router(extract_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(ServiceError)
async def service_error_handler(_: Request, exc: ServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )
