from __future__ import annotations

import re
from pathlib import Path

from app.models import ClassificationMetadata, ClassificationResult, PageChunk

from .taxonomy import CATEGORY_KEYWORDS, DOMAIN_KEYWORDS, TAG_HINTS


def _count_matches(text: str, terms: tuple[str, ...]) -> int:
    score = 0
    for term in terms:
        pattern = re.escape(term.lower())
        score += len(re.findall(pattern, text))
    return score


def _score_candidates(text: str, filename: str, rules: dict[str, tuple[str, ...]]) -> dict[str, int]:
    filename_lower = filename.lower()
    scores: dict[str, int] = {}
    for label, terms in rules.items():
        text_score = _count_matches(text, terms)
        filename_score = sum(2 for term in terms if term.lower().replace(" ", "_") in filename_lower or term.lower() in filename_lower)
        scores[label] = text_score + filename_score
    return scores


def _pick_label(scores: dict[str, int]) -> tuple[str, float]:
    label, score = max(scores.items(), key=lambda item: item[1], default=("unknown", 0))
    if score <= 0:
        return "unknown", 0.0
    confidence = min(0.99, 0.35 + (score / 10))
    return label, confidence


def _build_tags(text: str, category: str, domain: str) -> list[str]:
    tags: list[str] = []
    for value in (category, domain):
        if value != "unknown":
            tags.append(value)

    for tag, terms in TAG_HINTS.items():
        if _count_matches(text, terms) > 0:
            tags.append(tag)

    deduped: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        normalized = tag.strip().lower().replace(" ", "_")
        if normalized and normalized not in seen:
            seen.add(normalized)
            deduped.append(normalized)
    return deduped[:8]


def classify_document(file_name: str, pages: list[PageChunk]) -> ClassificationResult:
    corpus = "\n".join(page.text for page in pages if page.text).lower()
    filename = Path(file_name).name.lower()

    category_scores = _score_candidates(corpus, filename, CATEGORY_KEYWORDS)
    domain_scores = _score_candidates(corpus, filename, DOMAIN_KEYWORDS)

    category, category_confidence = _pick_label(category_scores)
    domain, domain_confidence = _pick_label(domain_scores)
    confidence = max(category_confidence, domain_confidence)
    tags = _build_tags(corpus, category, domain)

    return ClassificationResult(
        document_category=category,
        document_domain=domain,
        tags=tags,
        classification=ClassificationMetadata(
            confidence=confidence,
            method="rules",
            model="rules-v1",
        ),
    )
