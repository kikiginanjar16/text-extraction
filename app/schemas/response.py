from __future__ import annotations

from app.models import ExtractResponsePayload


def serialize_extract_response(payload: ExtractResponsePayload) -> dict[str, object]:
    return payload.as_dict()
