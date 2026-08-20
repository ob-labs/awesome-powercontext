from app.dependencies import build_default_container
from app.powercontext.runtime import (
    EmbeddedPowerContextMemory,
    powercontext_config,
)


def test_embedded_runtime_captures_searches_revises_and_retires_memory(tmp_path):
    database_path = tmp_path / "powercontext.db"
    memory = EmbeddedPowerContextMemory(
        config=powercontext_config(
            f"sqlite+aiosqlite:///{database_path.as_posix()}"
        ),
        scope_id="smart-ev-cockpit-test",
    )
    metadata = {
        "scenario_id": "smart_ev_cockpit",
        "vehicle_id": "demo_vehicle_001",
        "actor_id": "child_rear_left",
        "seat_position": "rear_left",
        "memory_kind": "media_preference",
        "source_event_ids": ["runtime-e2e-1"],
        "lifecycle_status": "active",
        "created_at": "2026-08-20T00:00:00Z",
    }

    try:
        added = memory.add(
            "The rear child prefers quiet bedtime stories.",
            user_id="child_rear_left",
            metadata=metadata,
            infer=False,
        )

        assert len(added["results"]) == 1
        added_row = added["results"][0]
        memory_id = added_row["id"]
        assert added_row["event"] == "ADD"
        assert added_row["powercontext"]["memory_ref"]["revision"] == 1
        source_refs = added_row["powercontext"]["source_refs"]
        assert len(source_refs) == 1
        assert source_refs[0]["source_type"] == "content"
        assert source_refs[0]["source_id"].startswith("smart-ev:")

        retried = memory.add(
            "The rear child prefers quiet bedtime stories.",
            user_id="child_rear_left",
            metadata=metadata,
            infer=False,
        )
        assert [row["id"] for row in retried["results"]] == [memory_id]
        assert len(memory.get_all(user_id="child_rear_left")["results"]) == 1

        searched = memory.search(
            query="quiet bedtime stories",
            user_id="child_rear_left",
            filters={"seat_position": "rear_left"},
            limit=5,
        )
        assert [row["id"] for row in searched["results"]] == [memory_id]
        assert searched["results"][0]["powercontext"]["matched_by"] == ["fts"]

        updated_metadata = {**metadata, "lifecycle_status": "archived"}
        updated = memory.update(
            memory_id=memory_id,
            content="The rear child prefers quiet audio stories.",
            metadata=updated_metadata,
        )
        assert updated["success"] is True
        assert updated["id"] == memory_id
        assert updated["powercontext"]["memory_ref"]["revision"] == 2

        listed = memory.get_all(
            user_id="child_rear_left",
            filters={"lifecycle_status": "archived"},
        )
        assert [row["memory"] for row in listed["results"]] == [
            "The rear child prefers quiet audio stories."
        ]

        assert memory.delete(memory_id=memory_id) is True
        assert memory.get_all(user_id="child_rear_left")["results"] == []
    finally:
        memory.close()


def test_powercontext_config_rejects_unsupported_database_url():
    try:
        powercontext_config("postgresql://localhost/powercontext")
    except ValueError as error:
        assert "sqlite+aiosqlite or mysql+aoceanbase" in str(error)
    else:
        raise AssertionError("unsupported database URL was accepted")


def test_default_container_seeds_and_searches_real_powercontext(tmp_path, monkeypatch):
    database_path = tmp_path / "container-powercontext.db"
    monkeypatch.setenv("POWERCONTEXT_BACKEND", "builtin")
    monkeypatch.setenv(
        "POWERCONTEXT_DATABASE_URL",
        f"sqlite+aiosqlite:///{database_path.as_posix()}",
    )
    monkeypatch.setenv("POWERCONTEXT_SCOPE_ID", "smart-ev-cockpit-container-test")
    monkeypatch.setenv("CHAT_HISTORY_DB_PATH", str(tmp_path / "chat.sqlite3"))
    monkeypatch.setenv("IDENTITY_DB_PATH", str(tmp_path / "identity.sqlite3"))
    monkeypatch.setenv("LLM_MODEL", "")
    monkeypatch.setenv("OPENAI_LLM_BASE_URL", "")

    container = build_default_container()
    try:
        assert container.powercontext_client.is_connected is True
        rows = container.powercontext_client.list_memories(limit=100)
        assert len(rows) == 8

        hits = container.powercontext_client.search_memories(
            query="river district restaurant",
            user_id="driver_primary",
            filters={
                "scenario_id": "smart_ev_cockpit",
                "memory_kind": "location_episode",
            },
            limit=5,
        )
        assert [hit["metadata"]["source_event_ids"] for hit in hits] == [
            ["seed_location_restaurant"]
        ]
        assert hits[0]["powercontext"]["matched_by"] == ["fts"]
    finally:
        container.close()

    assert container.powercontext_client.is_connected is False
