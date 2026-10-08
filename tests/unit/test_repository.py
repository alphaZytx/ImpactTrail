from __future__ import annotations

from datetime import UTC, datetime

from riskpulse.domain.documents import RawDocument, SourceType
from riskpulse.processing.normalize import normalize_document
from riskpulse.storage.repositories import Repository


def test_document_deduplication_by_content(repository: Repository) -> None:
    first = normalize_document(
        RawDocument(
            source_record_id="a",
            source="gdelt",
            source_type=SourceType.NEWS,
            text="Same normalized content",
            published_at=datetime.now(UTC),
        )
    )
    second = normalize_document(
        RawDocument(
            source_record_id="b",
            source="bluesky",
            source_type=SourceType.SOCIAL,
            text="Same normalized content",
            published_at=datetime.now(UTC),
        )
    )
    assert repository.save_document(first) is True
    assert repository.save_document(second) is False
    assert repository.metrics()["documents"] == 1


def test_clear_runtime(repository: Repository) -> None:
    repository.save_dead_letter("demo", "reason", {"record": 1})
    assert repository.metrics()["dead_letters"] == 1
    repository.clear_runtime()
    assert repository.metrics()["dead_letters"] == 0
