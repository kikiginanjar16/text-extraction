from __future__ import annotations

from app.core.errors import InvalidRequestError

VALID_PAGINATE_STRATEGIES = {"auto", "virtual"}


def normalize_paginate_strategy(value: str | None) -> str:
    normalized = (value or "auto").strip().lower()
    if normalized not in VALID_PAGINATE_STRATEGIES:
        raise InvalidRequestError("paginate_strategy must be one of: auto, virtual")
    return normalized
