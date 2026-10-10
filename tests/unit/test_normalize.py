from __future__ import annotations

from datetime import UTC, datetime

from impacttrail.domain.documents import RawDocument, SourceType
from impacttrail.processing.normalize import canonicalize_url, normalize_document, normalize_text


def test_normalize_text_collapses_whitespace_and_control_characters() -> None:
    assert normalize_text("  Profit\n\t growth\x00 today  ") == "Profit growth today"


def test_canonicalize_url_removes_tracking_and_fragment() -> None:
    url = "HTTPS://Example.org/story/?utm_source=x&keep=1#section"
    assert canonicalize_url(url) == "https://example.org/story?keep=1"


def test_normalize_document_has_stable_identity_and_hash() -> None:
    raw = RawDocument(
        source_record_id="1",
        source="gdelt",
        source_type=SourceType.NEWS,
        text=" Nova Bank profit growth ",
        url="https://example.org/a?utm_campaign=test",
        published_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    normalized = normalize_document(raw)
    assert normalized.document_id == "gdelt:1"
    assert normalized.canonical_url == "https://example.org/a"
    assert len(normalized.content_hash) == 64
