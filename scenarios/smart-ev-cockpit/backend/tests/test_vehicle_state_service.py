import pytest

from app.services.vehicle_state_service import UnsupportedVehicleField, VehicleStateService


def test_nested_hvac_patch_preserves_existing_leaf_and_adds_new_leaf():
    service = VehicleStateService()

    diff = service.apply_patch({"hvac": {"front_right_target_temp": 24}})

    assert service.current_state()["hvac"] == {
        "front_left_target_temp": 22,
        "front_right_target_temp": 24,
    }
    assert diff == [
        {
            "field": "hvac.front_right_target_temp",
            "before": None,
            "after": 24,
        }
    ]


def test_nested_patch_reports_only_changed_leaf_paths():
    service = VehicleStateService()

    diff = service.apply_patch(
        {
            "hvac": {"front_left_target_temp": 23},
            "seat_heat": {"front_left": 1, "front_right": 0},
        }
    )

    assert diff == [
        {
            "field": "hvac.front_left_target_temp",
            "before": 22,
            "after": 23,
        },
        {"field": "seat_heat.front_left", "before": 0, "after": 1},
    ]


def test_new_nested_dictionary_reports_deepest_leaf_path():
    service = VehicleStateService()

    diff = service.apply_patch({"hvac": {"rear": {"target_temp": 21}}})

    assert diff == [
        {
            "field": "hvac.rear.target_temp",
            "before": None,
            "after": 21,
        }
    ]


def test_apply_event_accepts_soc_and_range():
    service = VehicleStateService()

    diff = service.apply_event({"soc": 18, "range_km": 76})

    assert service.current_state()["soc"] == 18
    assert service.current_state()["range_km"] == 76
    assert [item["field"] for item in diff] == ["soc", "range_km"]


def test_apply_event_rejects_unknown_fields_without_mutating_state():
    service = VehicleStateService()
    before = service.current_state()

    with pytest.raises(UnsupportedVehicleField, match="admin"):
        service.apply_event({"soc": 18, "admin": True})

    assert service.current_state() == before


@pytest.mark.parametrize(
    "patch",
    [
        {"soc": {"raw": 18}},
        {"hvac": 24},
    ],
)
def test_apply_patch_rejects_dictionary_scalar_type_conflicts_atomically(patch: dict):
    service = VehicleStateService()
    before = service.current_state()

    with pytest.raises(ValueError, match="type conflict") as exc_info:
        service.apply_patch({"range_km": 76, **patch})

    assert type(exc_info.value).__name__ == "InvalidVehiclePatch"
    assert service.current_state() == before


def test_apply_event_rejects_type_conflicts_without_mutating_state():
    service = VehicleStateService()
    before = service.current_state()

    with pytest.raises(ValueError, match="hvac") as exc_info:
        service.apply_event({"soc": 18, "hvac": 24})

    assert type(exc_info.value).__name__ == "InvalidVehiclePatch"
    assert service.current_state() == before
