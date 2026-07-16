import csv
from pathlib import Path

import pytest

from app.data.csv_snapshot_loader import CsvSnapshotLoader

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


def write_csv(path: Path, fieldnames: list[str], row: dict[str, object]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(row)


@pytest.mark.parametrize(
    ("unsupported", "expected"),
    [
        ('["rest_mode", "pet_mode"]', ["rest_mode", "pet_mode"]),
        ("rest_mode, pet_mode", ["rest_mode", "pet_mode"]),
        ("rest_mode;pet_mode", ["rest_mode", "pet_mode"]),
        ("rest_mode", ["rest_mode"]),
    ],
)
def test_vehicle_profile_maps_allowlisted_fields_and_unsupported_formats(
    tmp_path: Path,
    unsupported: str,
    expected: list[str],
):
    vehicle_csv = tmp_path / "vehicle.csv"
    write_csv(
        vehicle_csv,
        VEHICLE_COLUMNS + ["owner_phone"],
        {
            "vehicle_id": "masked-001",
            "model_series_display_name": "ET5 Touring",
            "platform": "NT2.0",
            "nomi_version": "NOMI GPT",
            "un_support_funcs": unsupported,
            "owner_phone": "13812345678",
        },
    )

    result = CsvSnapshotLoader(vehicle_csv, tmp_path / "soa.csv").load_vehicle_profile()

    assert result.source == "masked_vehicle_csv"
    assert result.missing_columns == []
    assert result.data == {
        "vehicle_id": "masked-001",
        "display_name": "ET5 Touring",
        "model_family": "ET5 Touring",
        "platform_version": "NT2.0",
        "assistant_version": "NOMI GPT",
        "unsupported_features": expected,
    }
    assert "owner_phone" not in result.data


@pytest.mark.parametrize(
    "unsupported",
    [
        "rest_mode pet_mode",
        '["rest_mode", 1]',
        "unknown_single_value",
    ],
)
def test_invalid_unsupported_functions_falls_back(tmp_path: Path, unsupported: str):
    vehicle_csv = tmp_path / "vehicle.csv"
    write_csv(
        vehicle_csv,
        VEHICLE_COLUMNS,
        {
            "vehicle_id": "masked-001",
            "model_series_display_name": "ET5 Touring",
            "platform": "NT2.0",
            "nomi_version": "NOMI GPT",
            "un_support_funcs": unsupported,
        },
    )

    result = CsvSnapshotLoader(vehicle_csv, tmp_path / "soa.csv").load_vehicle_profile()

    assert result.source == "synthetic_fallback"
    assert result.data["vehicle_id"] == "demo_vehicle_001"


def test_malformed_csv_falls_back_instead_of_claiming_vehicle_source(tmp_path: Path):
    vehicle_csv = tmp_path / "vehicle.csv"
    vehicle_csv.write_text(
        ",".join(VEHICLE_COLUMNS)
        + '\nmasked-001,"ET5"oops,NT2.0,NOMI GPT,rest_mode',
        encoding="utf-8",
    )

    result = CsvSnapshotLoader(vehicle_csv, tmp_path / "soa.csv").load_vehicle_profile()

    assert result.source == "synthetic_fallback"


def test_malformed_trailing_csv_row_invalidates_whole_snapshot(tmp_path: Path):
    vehicle_csv = tmp_path / "vehicle.csv"
    vehicle_csv.write_text(
        ",".join(VEHICLE_COLUMNS)
        + "\nmasked-001,ET5 Touring,NT2.0,NOMI GPT,rest_mode"
        + '\nmasked-002,"ET5"oops,NT2.0,NOMI GPT,rest_mode',
        encoding="utf-8",
    )

    result = CsvSnapshotLoader(vehicle_csv, tmp_path / "soa.csv").load_vehicle_profile()

    assert result.source == "synthetic_fallback"


def test_missing_soa_columns_returns_labeled_synthetic_fallback(tmp_path: Path):
    soa_csv = tmp_path / "soa.csv"
    write_csv(soa_csv, ["soc", "remaining_range"], {"soc": 80, "remaining_range": 400})

    result = CsvSnapshotLoader(tmp_path / "vehicle.csv", soa_csv).load_telemetry()

    assert result.source == "synthetic_fallback"
    assert result.missing_columns == [
        "outside_temp_c",
        "incar_temp_c",
        "hvac_frnt_le_target_temp",
        "frnt_le_seat_ht_sts",
    ]
    assert result.data["soc"] == 62
    assert result.data["range_km"] == 305


def test_valid_soa_maps_fields_to_vehicle_state_names(tmp_path: Path):
    soa_csv = tmp_path / "soa.csv"
    write_csv(
        soa_csv,
        TELEMETRY_COLUMNS,
        {
            "soc": "81",
            "remaining_range": "412",
            "outside_temp_c": "7.5",
            "incar_temp_c": "20",
            "hvac_frnt_le_target_temp": "23",
            "frnt_le_seat_ht_sts": "2",
        },
    )

    result = CsvSnapshotLoader(tmp_path / "vehicle.csv", soa_csv).load_telemetry()

    assert result.source == "soa_csv"
    assert result.missing_columns == []
    assert result.data == {
        "soc": 81,
        "range_km": 412,
        "outside_temp_c": 7.5,
        "inside_temp_c": 20,
        "hvac": {"front_left_target_temp": 23},
        "seat_heat": {"front_left": 2},
    }


@pytest.mark.parametrize("non_finite", ["NaN", "Infinity", "-Infinity"])
def test_non_finite_telemetry_returns_synthetic_fallback(
    tmp_path: Path,
    non_finite: str,
):
    soa_csv = tmp_path / "soa.csv"
    write_csv(
        soa_csv,
        TELEMETRY_COLUMNS,
        {
            "soc": non_finite,
            "remaining_range": "412",
            "outside_temp_c": "7.5",
            "incar_temp_c": "20",
            "hvac_frnt_le_target_temp": "23",
            "frnt_le_seat_ht_sts": "2",
        },
    )

    result = CsvSnapshotLoader(tmp_path / "vehicle.csv", soa_csv).load_telemetry()

    assert result.source == "synthetic_fallback"
    assert result.data["soc"] == 62


def test_synthetic_telemetry_fallback_is_deep_copied_between_calls(tmp_path: Path):
    loader = CsvSnapshotLoader(tmp_path / "vehicle.csv", tmp_path / "soa.csv")

    first = loader.load_telemetry()
    first.data["hvac"]["front_left_target_temp"] = 99
    second = loader.load_telemetry()

    assert second.data["hvac"]["front_left_target_temp"] == 22


@pytest.mark.parametrize("kind", ["missing", "malformed"])
def test_missing_or_malformed_files_never_claim_csv_source(tmp_path: Path, kind: str):
    vehicle_csv = tmp_path / "vehicle.csv"
    soa_csv = tmp_path / "soa.csv"
    if kind == "malformed":
        vehicle_csv.write_bytes(b"\xff\xfe")
        soa_csv.write_bytes(b"\xff\xfe")

    loader = CsvSnapshotLoader(vehicle_csv, soa_csv)

    assert loader.load_vehicle_profile().source == "synthetic_fallback"
    assert loader.load_telemetry().source == "synthetic_fallback"
