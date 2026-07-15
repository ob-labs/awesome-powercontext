from app.domain.events import CockpitDialogueEvent, VehicleProfile


def validate_vehicle_profile(payload: dict) -> VehicleProfile:
    return VehicleProfile.model_validate(payload)


def validate_dialogue_events(rows: list[dict]) -> list[CockpitDialogueEvent]:
    return [CockpitDialogueEvent.model_validate(row) for row in rows]
