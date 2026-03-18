from __future__ import annotations

import secrets

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.api.routes.extract import router as extract_router
from app.core.config import get_settings
from app.core.errors import ServiceError
from app.core.logging import configure_logging

configure_logging()
settings = get_settings()
docs_security = HTTPBasic(auto_error=False)

app = FastAPI(
    title="Text Extraction API",
    version="0.1.0",
    summary="Extract text from supported document types into an ordered pages array.",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.include_router(extract_router)


def _swagger_auth_enabled() -> bool:
    return bool(settings.swagger_username and settings.swagger_password)


def require_swagger_auth(
    credentials: HTTPBasicCredentials | None = Depends(docs_security),
) -> None:
    if not _swagger_auth_enabled():
        return

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Swagger authentication required",
            headers={"WWW-Authenticate": "Basic"},
        )

    valid_username = secrets.compare_digest(credentials.username, settings.swagger_username or "")
    valid_password = secrets.compare_digest(credentials.password, settings.swagger_password or "")
    if not (valid_username and valid_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Swagger credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/openapi.json", include_in_schema=False)
async def openapi_json(_: None = Depends(require_swagger_auth)) -> JSONResponse:
    return JSONResponse(app.openapi())


@app.get("/docs", include_in_schema=False)
async def swagger_docs(_: None = Depends(require_swagger_auth)):
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=f"{app.title} - Swagger UI",
    )


@app.get("/redoc", include_in_schema=False)
async def redoc_docs(_: None = Depends(require_swagger_auth)):
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=f"{app.title} - ReDoc",
    )


@app.exception_handler(ServiceError)
async def service_error_handler(_: Request, exc: ServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )
