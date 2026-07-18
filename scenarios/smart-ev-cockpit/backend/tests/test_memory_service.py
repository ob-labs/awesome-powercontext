from app.domain.memory_models import MemoryMetadata, MemoryRecord
from app.powermem.client import PowerMemClient
from app.services.memory_service import MemoryService


def _raw(record: MemoryRecord) -> dict:
    return {
        "id": record.memory_id,
        "memory": record.content,
        "metadata": record.metadata.model_dump(mode="json"),
    }


def _record(
    memory_id: str,
    *,
    actor_id: str = "driver_primary",
    seat_position: str = "front_left",
    memory_kind: str = "cabin_control_preference",
) -> MemoryRecord:
    return MemoryRecord(
        memory_id=memory_id,
        content="driver winter preference target_temp_c=26; seat_heat_level=2",
        metadata=MemoryMetadata(
            actor_id=actor_id,
            seat_position=seat_position,
            memory_kind=memory_kind,
            created_at="2026-07-12T00:00:00Z",
            target_temp_c=26,
            seat_heat_level=2,
        ),
    )


def _search_hit(
    memory_id: str,
    content: str,
    *,
    confidence: float,
    created_at: str,
    source_event_ids: list[str],
    fts_rank: int | None = None,
    vector_rank: int | None = None,
    vector_similarity: float | None = None,
) -> dict:
    metadata = _record(memory_id).metadata.model_copy(
        update={
            "confidence": confidence,
            "created_at": created_at,
            "source_event_ids": source_event_ids,
            "memory_kind": "person_profile",
        }
    ).model_dump(mode="json")
    metadata["_fusion_info"] = {
        "fts_rank": fts_rank,
        "vector_rank": vector_rank,
    }
    if vector_similarity is not None:
        metadata["_vector_similarity"] = vector_similarity
    return {
        "id": memory_id,
        "memory": content,
        "metadata": metadata,
        "created_at": created_at,
    }


class SearchMissListHitPowerMem:
    def __init__(self, records: list[MemoryRecord]):
        self.records = records
        self.search_calls: list[dict] = []
        self.get_all_calls: list[dict] = []

    def search(self, **kwargs):
        self.search_calls.append(kwargs)
        return {"results": []}

    def get_all(self, **kwargs):
        self.get_all_calls.append(kwargs)
        filters = kwargs.get("filters") or {}
        if set(filters) - {"scenario_id", "vehicle_id"}:
            return {"results": []}
        return {"results": [_raw(record) for record in self.records]}


class RankedSearchPowerMem:
    def __init__(
        self,
        broad_results: list[dict],
        listed_results: list[dict] | None = None,
    ):
        self.broad_results = broad_results
        self.listed_results = listed_results or []
        self.search_calls: list[dict] = []
        self.get_all_calls: list[dict] = []

    def search(self, **kwargs):
        self.search_calls.append(kwargs)
        if set(kwargs.get("filters") or {}) - {"scenario_id", "vehicle_id"}:
            return {"results": []}
        return {"results": self.broad_results}

    def get_all(self, **kwargs):
        self.get_all_calls.append(kwargs)
        return {"results": self.listed_results}


def _chat_search(service: MemoryService, *, query: str, limit: int = 2):
    return service.search(
        query=query,
        user_id="driver_primary",
        filters={
            "scenario_id": "smart_ev_cockpit",
            "vehicle_id": "demo_vehicle_001",
            "actor_id": "driver_primary",
            "seat_position": "front_left",
        },
        limit=limit,
        prefer_recent_chat=True,
    )


def test_search_falls_back_to_list_and_filters_metadata_in_application():
    raw_memory = SearchMissListHitPowerMem(
        [
            _record("driver-cabin"),
            _record(
                "passenger-cabin",
                actor_id="passenger_front",
                seat_position="front_right",
            ),
        ]
    )
    service = MemoryService(PowerMemClient(raw_memory))

    records = service.search(
        query="cold cabin preferences and safety policy for driver_primary front_left",
        user_id="driver_primary",
        filters={
            "scenario_id": "smart_ev_cockpit",
            "vehicle_id": "demo_vehicle_001",
            "actor_id": "driver_primary",
            "seat_position": "front_left",
            "memory_kind": {
                "in": ["cabin_control_preference", "safety_policy"]
            },
        },
        limit=10,
    )

    assert [record.memory_id for record in records] == ["driver-cabin"]
    assert raw_memory.search_calls[0]["filters"] == {
        "scenario_id": "smart_ev_cockpit",
        "vehicle_id": "demo_vehicle_001",
        "actor_id": "driver_primary",
        "seat_position": "front_left",
        "memory_kind": {
            "in": ["cabin_control_preference", "safety_policy"]
        },
    }
    assert raw_memory.search_calls[1]["filters"] == {
        "scenario_id": "smart_ev_cockpit",
        "vehicle_id": "demo_vehicle_001",
    }
    assert raw_memory.get_all_calls == [
        {
            "filters": {
                "scenario_id": "smart_ev_cockpit",
                "vehicle_id": "demo_vehicle_001",
            },
            "user_id": "driver_primary",
            "limit": 2000,
        }
    ]


def test_search_promotes_relevant_recent_chat_memory_without_listing_merge():
    seed = _search_hit(
        "seed-high-confidence",
        "summer cabin temperature preference",
        confidence=0.99,
        created_at="2026-08-01T00:00:00Z",
        source_event_ids=["gen_comfort_001"],
        vector_rank=2,
    )
    coffee = _search_hit(
        "chat-coffee",
        "喜欢喝咖啡",
        confidence=0.8,
        created_at="2026-07-17T09:11:56Z",
        source_event_ids=["demo_session:trace_coffee:chat"],
        fts_rank=1,
        vector_rank=1,
    )
    raw = RankedSearchPowerMem(
        broad_results=[seed, coffee],
        listed_results=[seed],
    )

    records = _chat_search(
        MemoryService(PowerMemClient(raw)),
        query="我喜欢喝咖啡吗",
    )

    assert [record.memory_id for record in records] == [
        "chat-coffee",
        "seed-high-confidence",
    ]
    assert raw.get_all_calls == []


def test_search_does_not_promote_chat_memory_beyond_vector_relevance_window():
    weather_one = _search_hit(
        "weather-one",
        "vehicle outside temperature sensor",
        confidence=0.7,
        created_at="2026-07-16T00:00:00Z",
        source_event_ids=["gen_weather_001"],
        vector_rank=1,
    )
    weather_two = _search_hit(
        "weather-two",
        "live weather is unavailable",
        confidence=0.7,
        created_at="2026-07-16T00:00:01Z",
        source_event_ids=["gen_weather_002"],
        vector_rank=2,
    )
    coffee = _search_hit(
        "chat-coffee",
        "喜欢喝咖啡",
        confidence=1.0,
        created_at="2026-07-17T09:11:56Z",
        source_event_ids=["demo_session:trace_coffee:chat"],
        vector_rank=21,
    )
    raw = RankedSearchPowerMem([weather_one, weather_two, coffee])

    records = _chat_search(
        MemoryService(PowerMemClient(raw)),
        query="今天天气如何",
        limit=3,
    )

    assert [record.memory_id for record in records] == ["weather-one", "weather-two"]


def test_search_promotes_chat_memory_at_vector_relevance_boundary():
    seed = _search_hit(
        "seed",
        "historical preference",
        confidence=0.9,
        created_at="2026-08-01T00:00:00Z",
        source_event_ids=["gen_profile_001"],
        vector_rank=1,
    )
    chat = _search_hit(
        "chat-generic-preference",
        "喜欢喝咖啡",
        confidence=0.8,
        created_at="2026-07-17T09:11:56Z",
        source_event_ids=["demo_session:trace_preference:chat"],
        vector_rank=20,
        vector_similarity=0.5,
    )
    raw = RankedSearchPowerMem([seed, chat])

    records = _chat_search(
        MemoryService(PowerMemClient(raw)),
        query="我的偏好是什么",
        limit=2,
    )

    assert [record.memory_id for record in records] == [
        "chat-generic-preference",
        "seed",
    ]


def test_search_rejects_top_ranked_chat_memory_with_low_vector_similarity():
    coffee = _search_hit(
        "chat-coffee",
        "喜欢喝咖啡",
        confidence=0.8,
        created_at="2026-07-17T09:11:56Z",
        source_event_ids=["demo_session:trace_coffee:chat"],
        vector_rank=1,
        vector_similarity=0.44,
    )
    raw = RankedSearchPowerMem([coffee])

    records = _chat_search(
        MemoryService(PowerMemClient(raw)),
        query="今天天气如何",
        limit=1,
    )

    assert records == []


def test_search_orders_relevant_chat_memories_newest_first_before_seed():
    older_chat = _search_hit(
        "older-chat",
        "喜欢手冲咖啡",
        confidence=0.8,
        created_at="2026-07-16T09:00:00Z",
        source_event_ids=["demo_session:trace_older:chat"],
        fts_rank=2,
        vector_rank=2,
    )
    seed = _search_hit(
        "seed",
        "historical coffee preference",
        confidence=0.99,
        created_at="2026-08-01T00:00:00Z",
        source_event_ids=["gen_profile_001"],
        fts_rank=1,
        vector_rank=1,
    )
    newer_chat = _search_hit(
        "newer-chat",
        "喜欢无糖榛果咖啡",
        confidence=0.8,
        created_at="2026-07-17T09:00:00Z",
        source_event_ids=["demo_session:trace_newer:chat"],
        fts_rank=3,
        vector_rank=3,
    )
    raw = RankedSearchPowerMem([older_chat, seed, newer_chat])

    records = _chat_search(
        MemoryService(PowerMemClient(raw)),
        query="我的咖啡偏好是什么",
        limit=3,
    )

    assert [record.memory_id for record in records] == [
        "newer-chat",
        "older-chat",
        "seed",
    ]


def test_search_without_fusion_metadata_preserves_powermem_order():
    first = _search_hit(
        "first",
        "first semantic result",
        confidence=0.2,
        created_at="2026-07-01T00:00:00Z",
        source_event_ids=["gen_first"],
    )
    second = _search_hit(
        "second",
        "second semantic result",
        confidence=1.0,
        created_at="2026-08-01T00:00:00Z",
        source_event_ids=["demo_session:trace_second:chat"],
    )
    first["metadata"].pop("_fusion_info")
    second["metadata"].pop("_fusion_info")
    raw = RankedSearchPowerMem([first, second])

    records = _chat_search(
        MemoryService(PowerMemClient(raw)),
        query="preference",
    )

    assert [record.memory_id for record in records] == ["first", "second"]


def test_search_deduplicates_semantic_candidates_by_memory_id():
    coffee = _search_hit(
        "chat-coffee",
        "喜欢喝咖啡",
        confidence=0.8,
        created_at="2026-07-17T09:11:56Z",
        source_event_ids=["demo_session:trace_coffee:chat"],
        fts_rank=1,
        vector_rank=1,
    )
    raw = RankedSearchPowerMem([coffee, coffee])

    records = _chat_search(
        MemoryService(PowerMemClient(raw)),
        query="我喜欢喝咖啡吗",
        limit=5,
    )

    assert [record.memory_id for record in records] == ["chat-coffee"]


def test_search_deduplicates_semantic_candidates_by_normalized_content():
    first = _search_hit(
        "capability-first",
        "车辆的小憩模式能力由脱敏车型配置确认。",
        confidence=0.9,
        created_at="2026-07-17T09:11:56Z",
        source_event_ids=["gen_capability_000001"],
        vector_rank=1,
    )
    duplicate = _search_hit(
        "capability-duplicate",
        "  车辆的小憩模式能力由脱敏车型配置确认。  ",
        confidence=0.8,
        created_at="2026-07-16T09:11:56Z",
        source_event_ids=["gen_capability_000002"],
        vector_rank=2,
    )
    raw = RankedSearchPowerMem([first, duplicate])

    records = _chat_search(
        MemoryService(PowerMemClient(raw)),
        query="还有其他的吗",
        limit=5,
    )

    assert [record.memory_id for record in records] == ["capability-first"]
