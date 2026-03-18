from __future__ import annotations

import ipaddress
import mimetypes
import re
import shutil
import socket
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import mkdtemp
from typing import Protocol
from urllib import error, parse, request

from app.core.errors import ExtractionFailedError, FileTooLargeError, InvalidRequestError


class UploadLike(Protocol):
    filename: str | None

    async def read(self, size: int = -1) -> bytes:
        ...


@dataclass(slots=True)
class PersistedUpload:
    original_name: str
    path: Path
    size_bytes: int
    temp_dir: Path


def _allocate_temp_path(original_name: str) -> tuple[Path, Path]:
    suffix = Path(original_name).suffix
    temp_dir = Path(mkdtemp(prefix="text-extraction-"))
    return temp_dir, temp_dir / f"source{suffix}"


async def persist_upload(upload: UploadLike, *, max_size_bytes: int) -> PersistedUpload:
    original_name = upload.filename or "upload.bin"
    size_bytes = 0
    temp_dir, tmp_path = _allocate_temp_path(original_name)

    try:
        with tmp_path.open("wb") as handle:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                size_bytes += len(chunk)
                if size_bytes > max_size_bytes:
                    raise FileTooLargeError("Maximum file size is 50 MB")
                handle.write(chunk)
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise

    return PersistedUpload(
        original_name=original_name,
        path=tmp_path,
        size_bytes=size_bytes,
        temp_dir=temp_dir,
    )


def cleanup_persisted_upload(persisted: PersistedUpload) -> None:
    shutil.rmtree(persisted.temp_dir, ignore_errors=True)


@asynccontextmanager
async def temporary_upload(upload: UploadLike, *, max_size_bytes: int):
    persisted = await persist_upload(upload, max_size_bytes=max_size_bytes)
    try:
        yield persisted
    finally:
        cleanup_persisted_upload(persisted)


def validate_remote_url(url: str) -> parse.SplitResult:
    parsed = parse.urlsplit(url.strip())
    if parsed.scheme not in {"http", "https"}:
        raise InvalidRequestError("URL must use http or https")
    if not parsed.hostname:
        raise InvalidRequestError("URL must include a valid hostname")

    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise ExtractionFailedError("Remote URL could not be resolved") from exc

    # Reject loopback/private targets to reduce SSRF risk.
    for address in addresses:
        candidate = ipaddress.ip_address(address[4][0])
        if (
            candidate.is_private
            or candidate.is_loopback
            or candidate.is_link_local
            or candidate.is_multicast
            or candidate.is_reserved
            or candidate.is_unspecified
        ):
            raise InvalidRequestError("Remote URL points to a private or restricted address")

    return parsed


def _guess_remote_name(url: str, headers: object) -> str:
    content_disposition = getattr(headers, "get", lambda *_: None)("Content-Disposition")
    if isinstance(content_disposition, str):
        match = re.search(r'filename="?([^";]+)"?', content_disposition)
        if match:
            return Path(match.group(1)).name

    parsed = parse.urlsplit(url)
    candidate = Path(parsed.path).name
    if candidate:
        return candidate

    content_type = getattr(headers, "get", lambda *_: None)("Content-Type")
    extension = ""
    if isinstance(content_type, str):
        extension = mimetypes.guess_extension(content_type.split(";", 1)[0].strip()) or ""
    return f"downloaded{extension or '.bin'}"


class _NoRedirectHandler(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        return None


def download_remote_file(url: str, *, max_size_bytes: int, timeout_sec: int) -> PersistedUpload:
    validate_remote_url(url)
    opener = request.build_opener(_NoRedirectHandler)
    req = request.Request(url, headers={"User-Agent": "text-extraction/0.1"})

    try:
        response = opener.open(req, timeout=timeout_sec)
    except error.HTTPError as exc:
        if exc.code in {301, 302, 303, 307, 308}:
            location = exc.headers.get("Location")
            if not location:
                raise ExtractionFailedError("Remote URL redirected without a target") from exc
            redirected = parse.urljoin(url, location)
            return download_remote_file(
                redirected,
                max_size_bytes=max_size_bytes,
                timeout_sec=timeout_sec,
            )
        raise ExtractionFailedError("Remote file could not be fetched") from exc
    except error.URLError as exc:
        raise ExtractionFailedError("Remote file could not be fetched") from exc

    original_name = _guess_remote_name(response.geturl(), response.headers)
    size_bytes = 0
    temp_dir, tmp_path = _allocate_temp_path(original_name)

    try:
        with response:
            with tmp_path.open("wb") as handle:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    size_bytes += len(chunk)
                    if size_bytes > max_size_bytes:
                        raise FileTooLargeError("Maximum file size is 50 MB")
                    handle.write(chunk)
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise

    return PersistedUpload(
        original_name=original_name,
        path=tmp_path,
        size_bytes=size_bytes,
        temp_dir=temp_dir,
    )
