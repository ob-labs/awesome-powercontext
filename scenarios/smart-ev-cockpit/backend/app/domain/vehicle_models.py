from pydantic import BaseModel, Field


class VehicleState(BaseModel):
    soc: int = 62
    range_km: int = 305
    inside_temp_c: float = 22
    outside_temp_c: float = 6
    drive_mode: str = "comfort"
    hvac: dict = Field(default_factory=dict)
    seat_heat: dict = Field(default_factory=dict)


class VehicleStateDiff(BaseModel):
    field: str
    before: object
    after: object
