from app.domain.memory_models import MemoryMetadata, MemoryRecord
from app.powercontext.client import PowerContextClient
from app.services.identity_service import IdentityService


class ProfileMemory:
    def __init__(self, records):
        self.records = records
        self.get_all_calls = []

    def get_all(self, *, filters=None, user_id=None, limit=100):
        self.get_all_calls.append(
            {"filters": filters, "user_id": user_id, "limit": limit}
        )
        return {
            "results": [
                {
                    "id": record.memory_id,
                    "memory": record.content,
                    "metadata": record.metadata.model_dump(mode="json"),
                }
                for record in self.records
            ]
        }


def _memory(memory_id: str, *, kind: str, content: str) -> MemoryRecord:
    return MemoryRecord(
        memory_id=memory_id,
        content=content,
        metadata=MemoryMetadata(
            actor_id="driver_primary",
            seat_position="front_left",
            memory_kind=kind,
            memory_dimension=["profile"] if kind == "person_profile" else ["preference"],
            created_at="2026-07-10T00:00:00Z",
        ),
    )


def test_identity_service_creates_default_actor_bindings(tmp_path):
    service = IdentityService(tmp_path / "identities.sqlite3")

    identities = service.list_identities()

    assert [identity.actor_id for identity in identities] == [
        "driver_primary",
        "passenger_front",
        "child_rear_left",
    ]
    assert identities[0].user_id == "driver_primary"
    assert identities[0].seat_position == "front_left"


def test_identity_service_persists_updated_user_binding(tmp_path):
    service = IdentityService(tmp_path / "identities.sqlite3")

    updated = service.update_identity(
        "driver_primary",
        user_id="guest_alex",
        display_name="Alex",
        profile_note="Temporary demo driver",
    )
    reloaded = IdentityService(tmp_path / "identities.sqlite3").get_identity(
        "driver_primary"
    )

    assert updated.user_id == "guest_alex"
    assert reloaded.user_id == "guest_alex"
    assert reloaded.display_name == "Alex"
    assert reloaded.profile_note == "Temporary demo driver"


def test_identity_service_builds_powercontext_profile_summary_for_bound_user(tmp_path):
    memory = ProfileMemory(
        [
            _memory(
                "profile-1",
                kind="person_profile",
                content="Alex profile links driver seat with quiet assistant wording.",
            ),
            _memory(
                "media-1",
                kind="media_preference",
                content="Alex prefers relaxed playlists at volume 18.",
            ),
        ]
    )
    service = IdentityService(tmp_path / "identities.sqlite3")
    service.update_identity("driver_primary", user_id="guest_alex")

    profile = service.get_profile(
        "driver_primary",
        powercontext_client=PowerContextClient(memory),
    )

    assert memory.get_all_calls[0]["user_id"] == "guest_alex"
    assert memory.get_all_calls[0]["filters"] == {
        "scenario_id": "smart_ev_cockpit",
        "vehicle_id": "demo_vehicle_001",
    }
    assert profile.identity.user_id == "guest_alex"
    assert profile.primary_memory == "Alex profile links driver seat with quiet assistant wording."
    assert profile.memory_kind_counts == {
        "media_preference": 1,
        "person_profile": 1,
    }
    assert [memory.memory_id for memory in profile.memories] == ["profile-1", "media-1"]
