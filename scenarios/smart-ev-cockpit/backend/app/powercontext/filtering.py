from collections.abc import Iterable
from typing import Any

from app.domain.memory_models import MemoryRecord

SERVER_FILTER_KEYS = {"scenario_id", "vehicle_id"}
FALLBACK_READ_LIMIT = 2000


def powercontext_server_filters(filters: dict | None) -> dict:
    if not filters:
        return {}
    return {
        key: value
        for key, value in filters.items()
        if key in SERVER_FILTER_KEYS
    }


def needs_server_filter_fallback(filters: dict | None) -> bool:
    requested = filters or {}
    return requested != powercontext_server_filters(requested)


def fallback_read_limit(limit: int) -> int:
    return max(limit, FALLBACK_READ_LIMIT)


def records_matching_filters(
    records: Iterable[MemoryRecord],
    filters: dict | None,
) -> list[MemoryRecord]:
    return [
        record
        for record in records
        if record_matches_filters(record, filters)
    ]


def record_matches_filters(
    record: MemoryRecord,
    filters: dict | None,
) -> bool:
    for key, expected in (filters or {}).items():
        if not _value_matches(_record_filter_value(record, key), expected):
            return False
    return True


def _record_filter_value(record: MemoryRecord, key: str) -> Any:
    if key in {"id", "memory_id"}:
        return record.memory_id
    return getattr(record.metadata, key, None)


def _value_matches(actual: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        if "in" in expected:
            return actual in set(expected["in"])
        return actual == expected
    return actual == expected
