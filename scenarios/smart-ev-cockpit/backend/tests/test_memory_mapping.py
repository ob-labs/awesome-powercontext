from pathlib import Path

from app.data.loader import load_json, load_jsonl
from app.domain.events import CockpitDialogueEvent, VehicleProfile

DATA_ROOT = Path(__file__).resolve().parents[2] / "data" / "synthetic"


def test_vehicle_profile_loads_with_neutral_branding():
    profile = VehicleProfile.model_validate(load_json(DATA_ROOT / "vehicle_profile.json"))

    assert profile.vehicle_id == "demo_vehicle_001"
    assert profile.display_name == "Demo Vehicle"
    serialized = profile.model_dump_json().lower()
    forbidden_public_tokens = ("".join(("n", "io")), "".join(("no", "mi")))
    assert all(token not in serialized for token in forbidden_public_tokens)


def test_dialogue_events_include_privacy_test_content():
    rows = load_jsonl(DATA_ROOT / "cockpit_dialogue_events.jsonl")
    events = [CockpitDialogueEvent.model_validate(row) for row in rows]

    assert {event.actor_id for event in events} >= {
        "driver_primary",
        "passenger_front",
        "child_rear_left",
    }
    assert any("123 Lake Rd" in event.query for event in events)
