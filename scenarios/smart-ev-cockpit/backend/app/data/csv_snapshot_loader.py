import csv
import json
import math
import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path

VEHICLE_COLUMNS = [
    "vehicle_id",
    "model_series_display_name",
    "platform",
    "nomi_version",
    "un_support_funcs",
]
TELEMETRY_COLUMNS = [
    "soc",
    "remaining_range",
    "outside_temp_c",
    "incar_temp_c",
    "hvac_frnt_le_target_temp",
    "frnt_le_seat_ht_sts",
]
KNOWN_UNSUPPORTED_FUNCTIONS = {"rest_mode", "pet_mode"}
SYNTHETIC_TELEMETRY = {
    "soc": 62,
    "range_km": 305,
    "outside_temp_c": 6,
    "inside_temp_c": 22,
    "hvac": {"front_left_target_temp": 22},
    "seat_heat": {"front_left": 0},
}


@dataclass(frozen=True)
class SnapshotResult:
    data: dict
    source: str
    missing_columns: list[str]


class CsvSnapshotLoader:
    def __init__(self, vehicle_csv: Path, soa_csv: Path):
        self.vehicle_csv = vehicle_csv
        self.soa_csv = soa_csv

    def load_vehicle_profile(self) -> SnapshotResult:
        row, missing = self._read_required_row(self.vehicle_csv, VEHICLE_COLUMNS)
        if row is None:
            return SnapshotResult(self._synthetic_vehicle_profile(), "synthetic_fallback", missing)

        try:
            model_name = row["model_series_display_name"].strip()
            data = {
                "vehicle_id": row["vehicle_id"].strip(),
                "display_name": model_name,
                "model_family": model_name,
                "platform_version": row["platform"].strip(),
                "assistant_version": row["nomi_version"].strip(),
                "unsupported_features": self._parse_unsupported(row["un_support_funcs"]),
            }
        except (json.JSONDecodeError, TypeError, ValueError):
            return SnapshotResult(
                self._synthetic_vehicle_profile(),
                "synthetic_fallback",
                missing,
            )
        return SnapshotResult(data, "masked_vehicle_csv", [])

    def load_telemetry(self) -> SnapshotResult:
        row, missing = self._read_required_row(self.soa_csv, TELEMETRY_COLUMNS)
        if row is None:
            return SnapshotResult(deepcopy(SYNTHETIC_TELEMETRY), "synthetic_fallback", missing)

        try:
            data = {
                "soc": self._number(row["soc"]),
                "range_km": self._number(row["remaining_range"]),
                "outside_temp_c": self._number(row["outside_temp_c"]),
                "inside_temp_c": self._number(row["incar_temp_c"]),
                "hvac": {
                    "front_left_target_temp": self._number(
                        row["hvac_frnt_le_target_temp"]
                    )
                },
                "seat_heat": {
                    "front_left": self._number(row["frnt_le_seat_ht_sts"])
                },
            }
        except (TypeError, ValueError):
            return SnapshotResult(deepcopy(SYNTHETIC_TELEMETRY), "synthetic_fallback", missing)
        return SnapshotResult(data, "soa_csv", [])

    @staticmethod
    def _read_required_row(
        path: Path,
        required_columns: list[str],
    ) -> tuple[dict[str, str] | None, list[str]]:
        try:
            with path.open("r", encoding="utf-8", newline="") as file:
                reader = csv.DictReader(file, strict=True)
                fieldnames = reader.fieldnames or []
                if len(fieldnames) != len(set(fieldnames)):
                    return None, required_columns.copy()
                missing = [column for column in required_columns if column not in fieldnames]
                rows = list(reader)
        except (OSError, UnicodeError, csv.Error):
            return None, required_columns.copy()

        if any(None in candidate or None in candidate.values() for candidate in rows):
            return None, required_columns.copy()
        row = rows[0] if rows else None
        if row is None:
            return None, missing or required_columns.copy()
        missing.extend(
            column
            for column in required_columns
            if column not in missing and not (row.get(column) or "").strip()
        )
        return (None, missing) if missing else (row, [])

    @staticmethod
    def _parse_unsupported(raw: str) -> list[str]:
        stripped = raw.strip()
        if stripped.startswith("["):
            values = json.loads(stripped)
            if not isinstance(values, list) or not all(
                isinstance(value, str) and value.strip() for value in values
            ):
                raise ValueError("unsupported functions must be a string array")
            return [value.strip() for value in values]
        if "," in stripped or ";" in stripped:
            values = [value.strip() for value in re.split(r"[,;]", stripped)]
            if any(not value for value in values):
                raise ValueError("unsupported functions contain an empty list item")
            return values
        if stripped in KNOWN_UNSUPPORTED_FUNCTIONS:
            return [stripped]
        raise ValueError("unsupported functions require a recognized list format")

    @staticmethod
    def _number(raw: str) -> int | float:
        value = float(raw)
        if not math.isfinite(value):
            raise ValueError("telemetry must be finite")
        return int(value) if value.is_integer() else value

    @staticmethod
    def _synthetic_vehicle_profile() -> dict:
        profile_path = (
            Path(__file__).resolve().parents[3] / "data" / "synthetic" / "vehicle_profile.json"
        )
        with profile_path.open("r", encoding="utf-8") as file:
            return json.load(file)
