from copy import deepcopy


class UnsupportedVehicleField(ValueError):
    pass


class InvalidVehiclePatch(ValueError):
    pass


class VehicleStateService:
    EVENT_FIELDS = {
        "soc",
        "range_km",
        "outside_temp_c",
        "inside_temp_c",
        "drive_mode",
        "hvac",
        "seat_heat",
        "navigation",
    }

    def __init__(self):
        self._state = {
            "soc": 62,
            "range_km": 305,
            "inside_temp_c": 22,
            "outside_temp_c": 6,
            "drive_mode": "comfort",
            "hvac": {"front_left_target_temp": 22},
            "seat_heat": {"front_left": 0, "front_right": 0},
        }

    def current_state(self) -> dict:
        return deepcopy(self._state)

    def apply_patch(self, patch: dict) -> list[dict]:
        self._validate_patch(self._state, patch)
        diff: list[dict] = []
        self._merge(self._state, patch, "", diff)
        return diff

    def apply_event(self, event: dict) -> list[dict]:
        unsupported = [field for field in event if field not in self.EVENT_FIELDS]
        if unsupported:
            raise UnsupportedVehicleField(
                f"Unsupported vehicle field: {', '.join(unsupported)}"
            )
        return self.apply_patch(event)

    @classmethod
    def _validate_patch(cls, state: dict, patch: dict, prefix: str = "") -> None:
        for key, value in patch.items():
            if key not in state:
                continue
            field = f"{prefix}.{key}" if prefix else key
            before = state[key]
            if isinstance(before, dict) != isinstance(value, dict):
                raise InvalidVehiclePatch(f"Vehicle field type conflict at {field}")
            if isinstance(value, dict):
                cls._validate_patch(before, value, field)

    @classmethod
    def _merge(
        cls,
        state: dict,
        patch: dict,
        prefix: str,
        diff: list[dict],
    ) -> None:
        for key, value in patch.items():
            field = f"{prefix}.{key}" if prefix else key
            before = state.get(key)
            if isinstance(value, dict):
                if not isinstance(before, dict):
                    state[key] = {}
                cls._merge(state[key], value, field, diff)
                continue
            if before != value:
                state[key] = deepcopy(value)
                diff.append({"field": field, "before": deepcopy(before), "after": deepcopy(value)})
