from __future__ import annotations

import hashlib
import re
import unicodedata
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from impacttrail.domain.documents import NormalizedDocument, RawDocument

_TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"}


def normalize_text(text: str, max_length: int = 8000) -> str:
    cleaned = unicodedata.normalize("NFKC", text)
    cleaned = re.sub(r"[\u0000-\u0008\u000b\u000c\u000e-\u001f]", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:max_length]


def canonicalize_url(url: str | None) -> str | None:
    if not url:
        return None
    parts = urlsplit(url)
    query = [(key, value) for key, value in parse_qsl(parts.query) if key not in _TRACKING_PARAMS]
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ""))


def normalize_document(raw: RawDocument, max_length: int = 8000) -> NormalizedDocument:
    text = normalize_text(raw.text, max_length=max_length)
    if not text:
        raise ValueError("Document is empty after normalization")
    content_hash = hashlib.sha256(text.casefold().encode("utf-8")).hexdigest()
    document_id = f"{raw.source}:{raw.source_record_id}"
    return NormalizedDocument(
        document_id=document_id,
        source_record_id=raw.source_record_id,
        source=raw.source,
        source_type=raw.source_type,
        text=text,
        canonical_url=canonicalize_url(str(raw.url)) if raw.url else None,
        published_at=raw.published_at,
        ingested_at=raw.ingested_at,
        author=raw.author,
        language=str(raw.raw_metadata.get("language") or "en").lower(),
        content_hash=content_hash,
        raw_metadata=raw.raw_metadata,
        is_replay=raw.is_replay,
    )
