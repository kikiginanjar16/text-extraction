from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib import error, request

from app.core.config import Settings
from app.models import EnrichmentMetadata, EnrichmentResult, PageChunk

from .base import EnrichmentProviderError


class OpenAIEnrichmentProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def enrich(
        self,
        *,
        api_key: str,
        file_name: str,
        document_category: str,
        document_domain: str,
        baseline_tags: list[str],
        pages: list[PageChunk],
    ) -> EnrichmentResult:
        excerpt = self._build_excerpt(pages)
        if not excerpt:
            raise EnrichmentProviderError("No text available for AI enrichment")

        payload = {
            "model": self.settings.openai_model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You improve document metadata. Return strict JSON with keys "
                        "'summary' and 'tags'. Summary must be concise, in Indonesian, "
                        "and no more than 2 sentences. Tags must be a JSON array with 3 to 8 "
                        "lowercase snake_case strings."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"file_name: {Path(file_name).name}\n"
                        f"document_category: {document_category}\n"
                        f"document_domain: {document_domain}\n"
                        f"baseline_tags: {', '.join(baseline_tags) or 'none'}\n\n"
                        f"document_excerpt:\n{excerpt}"
                    ),
                },
            ],
        }

        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.settings.openai_api_base}/chat/completions",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )

        try:
            with request.urlopen(req, timeout=self.settings.openai_timeout_sec) as response:
                raw_payload = json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            raise EnrichmentProviderError(f"OpenAI request failed with status {exc.code}") from exc
        except error.URLError as exc:
            raise EnrichmentProviderError("OpenAI request failed") from exc
        except TimeoutError as exc:
            raise EnrichmentProviderError("OpenAI request timed out") from exc

        content = self._extract_content(raw_payload)
        parsed = self._parse_content(content)
        summary = parsed.get("summary")
        tags = parsed.get("tags")
        if not isinstance(summary, str) or not summary.strip():
            raise EnrichmentProviderError("OpenAI response did not include a valid summary")
        if not isinstance(tags, list) or not tags:
            raise EnrichmentProviderError("OpenAI response did not include valid tags")

        normalized_tags = []
        seen: set[str] = set()
        for tag in tags:
            if not isinstance(tag, str):
                continue
            normalized = tag.strip().lower().replace(" ", "_")
            if normalized and normalized not in seen:
                seen.add(normalized)
                normalized_tags.append(normalized)

        if not normalized_tags:
            raise EnrichmentProviderError("OpenAI response produced no usable tags")

        return EnrichmentResult(
            summary=summary.strip(),
            tags=normalized_tags[:8],
            enrichment=EnrichmentMetadata(
                status="applied",
                ai_used=True,
                provider="openai",
                model=raw_payload.get("model", self.settings.openai_model),
            ),
        )

    def _build_excerpt(self, pages: list[PageChunk]) -> str:
        text = "\n\n".join(page.text for page in pages if page.text.strip())
        return text[: self.settings.openai_excerpt_chars]

    def _extract_content(self, payload: dict[str, Any]) -> str:
        try:
            message = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise EnrichmentProviderError("Unexpected OpenAI response shape") from exc
        if isinstance(message, str):
            return message
        if isinstance(message, list):
            parts = []
            for item in message:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(str(item.get("text", "")))
            return "".join(parts)
        raise EnrichmentProviderError("Unexpected OpenAI content type")

    def _parse_content(self, content: str) -> dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise EnrichmentProviderError("OpenAI did not return valid JSON") from exc
