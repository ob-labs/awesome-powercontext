import pytest

from app.domain.memory_models import MemoryMetadata, MemoryRecord
from app.powermem.client import PowerMemClient
from app.services.lifecycle_service import LifecycleService
from app.services.vehicle_state_service import VehicleStateService
from tests.fakes import CrudPowerMem, memory_record


def test_day_90_decays_expired_temporary_memory():
    service = LifecycleService()
    memory = MemoryRecord(
        memory_id="mem_temp",
        content="driver_primary preferred 24C during a business trip.",
        metadata=MemoryMetadata(
            actor_id="driver_primary",
            memory_kind="temporary_context",
            memory_dimension=["lifecycle"],
            memory_layer="short_term",
            created_at="2026-03-01T00:00:00Z",
            valid_until="2026-03-15",
            retention_score=0.75,
        ),
    )

    updated = service.apply_clock(memory, current_day=90)

    assert updated.metadata.lifecycle_status == "decayed"
    assert updated.metadata.retention_score == 0.18


def test_vehicle_state_service_returns_before_after_diff():
    service = VehicleStateService()

    diff = service.apply_patch({"soc": 18, "range_km": 76})

    assert {"field": "soc", "before": 62, "after": 18} in diff
    assert {"field": "range_km", "before": 305, "after": 76} in diff


def test_plan_keeps_durable_preferences_and_plans_temporary_mutations():
    service = LifecycleService()
    memories = [
        memory_record(
            "durable",
            metadata_updates={
                "memory_kind": "driving_preference",
                "memory_layer": "long_term",
                "lifecycle_status": "active",
            },
        ),
        memory_record(
            "decay",
            metadata_updates={"retention_score": 0.8, "lifecycle_status": "active"},
        ),
        memory_record(
            "archive",
            metadata_updates={"retention_score": 0.2, "lifecycle_status": "decayed"},
        ),
        memory_record(
            "delete",
            metadata_updates={
                "retention_policy": "expire_after_valid_until",
                "valid_until": "2026-03-15",
            },
        ),
    ]

    plan = service.plan(memories, current_day=90)

    assert [(item.type, item.memory_id, item.after_status) for item in plan] == [
        ("UPDATE", "archive", "archived"),
        ("UPDATE", "decay", "decayed"),
        ("DELETE", "delete", "deleted"),
    ]
    assert all(item.memory_id != "durable" for item in plan)


def test_execute_uses_original_non_empty_content_and_real_delete():
    fake = CrudPowerMem()
    service = LifecycleService(PowerMemClient(fake))
    memories = [
        memory_record(
            "update",
            content="original temporary context",
            metadata_updates={"retention_score": 0.8},
        ),
        memory_record(
            "delete",
            metadata_updates={
                "retention_policy": "expire_after_valid_until",
                "valid_until": "2026-03-15",
            },
        ),
    ]

    result = service.run(memories, current_day=90)

    assert result.failed_operation is None
    assert fake.update_calls[0]["content"] == "original temporary context"
    assert fake.delete_calls == [{"memory_id": "delete"}]
    assert [item["memory_id"] for item in result.completed_operations] == [
        "delete",
        "update",
    ]
    assert all("before_status" in item and "after_status" in item for item in result.audit)


@pytest.mark.parametrize(
    "valid_until",
    [None, "2026-04-01", "2026-04-01T00:00:00Z", "not-a-date"],
)
def test_delete_requires_valid_expired_valid_until(valid_until):
    service = LifecycleService()
    memory = memory_record(
        "delete-candidate",
        metadata_updates={
            "retention_policy": "expire_after_valid_until",
            "valid_until": valid_until,
        },
    )

    plan = service.plan([memory], current_day=90)

    assert all(operation.type != "DELETE" for operation in plan)


@pytest.mark.parametrize(
    ("valid_until", "should_delete"),
    [
        ("2026-03-15T08:30:00Z", True),
        ("2026-04-15T08:30:00Z", False),
        ("2026-03-15T08:30:00+08:00", True),
    ],
)
def test_delete_parses_generator_iso_datetime_formats(valid_until, should_delete):
    memory = memory_record(
        "generated-temp",
        metadata_updates={
            "retention_policy": "expire_after_valid_until",
            "valid_until": valid_until,
        },
    )

    plan = LifecycleService().plan([memory], current_day=90)

    assert any(operation.type == "DELETE" for operation in plan) is should_delete


class UpdateResultPowerMem(CrudPowerMem):
    def __init__(self, update_result):
        super().__init__()
        self.update_result = update_result

    def update(self, *, memory_id: str, content: str, metadata: dict):
        self.update_calls.append(
            {"memory_id": memory_id, "content": content, "metadata": metadata}
        )
        return self.update_result


@pytest.mark.parametrize(
    "update_result",
    [None, False, {}, {"success": False}, {"error": "update rejected"}],
)
def test_update_non_success_response_stops_and_reports_failure(update_result):
    fake = UpdateResultPowerMem(update_result)
    service = LifecycleService(PowerMemClient(fake))

    with pytest.raises(Exception) as caught:
        service.run(
            [
                memory_record("a", metadata_updates={"retention_score": 0.8}),
                memory_record("b", metadata_updates={"retention_score": 0.8}),
            ],
            current_day=90,
        )

    error = caught.value
    assert error.completed_operations == []
    assert error.failed_operation["memory_id"] == "a"
    assert error.failed_operation["result"] == "failed"
    assert [call["memory_id"] for call in fake.update_calls] == ["a"]


@pytest.mark.parametrize(
    "update_result",
    [
        True,
        {"success": True},
        {
            "id": "a",
            "memory": "memory content",
            "metadata": {"lifecycle_status": "decayed"},
        },
    ],
)
def test_update_accepts_real_powermem_success_shapes(update_result):
    fake = UpdateResultPowerMem(update_result)

    result = LifecycleService(PowerMemClient(fake)).run(
        [memory_record("a", metadata_updates={"retention_score": 0.8})],
        current_day=90,
    )

    assert [operation["memory_id"] for operation in result.completed_operations] == ["a"]
    assert result.failed_operation is None


def test_empty_content_is_not_planned_for_update_and_is_audited_as_skipped():
    fake = CrudPowerMem()
    service = LifecycleService(PowerMemClient(fake))
    memory = memory_record(
        "empty",
        content="   ",
        metadata_updates={"retention_score": 0.8},
    )

    result = service.run([memory], current_day=90)

    assert result.plan == []
    assert result.completed_operations == []
    assert result.audit == [
        {
            "type": "UPDATE",
            "memory_id": "empty",
            "memory_ids": ["empty"],
            "before_status": "active",
            "after_status": "decayed",
            "result": "skipped",
            "reason": "empty_content",
        }
    ]
    assert fake.update_calls == []


def test_run_reports_no_candidate_audit_when_lifecycle_has_nothing_to_mutate():
    fake = CrudPowerMem()
    service = LifecycleService(PowerMemClient(fake))

    result = service.run(
        [
            memory_record(
                "durable",
                metadata_updates={
                    "memory_kind": "driving_preference",
                    "memory_layer": "long_term",
                },
            )
        ],
        current_day=90,
    )

    assert result.plan == []
    assert result.completed_operations == []
    assert result.audit == [
        {
            "type": "REVIEW",
            "memory_id": "lifecycle-review",
            "memory_ids": [],
            "before_status": "active",
            "after_status": "unchanged",
            "result": "no_candidates",
            "reason": "no_temporary_context_due",
        }
    ]


def test_run_reports_no_candidate_audit_when_temporary_memories_are_not_due():
    fake = CrudPowerMem()
    service = LifecycleService(PowerMemClient(fake))

    result = service.run(
        [
            memory_record(
                "future-temp",
                metadata_updates={
                    "retention_policy": "expire_after_valid_until",
                    "valid_until": "2026-04-15T00:00:00Z",
                },
            )
        ],
        current_day=90,
    )

    assert result.plan == []
    assert result.completed_operations == []
    assert result.audit[0]["type"] == "REVIEW"
    assert result.audit[0]["result"] == "no_candidates"


class FailingCrudPowerMem(CrudPowerMem):
    def update(self, *, memory_id: str, content: str, metadata: dict) -> dict:
        if memory_id == "b":
            raise RuntimeError("planned failure")
        return super().update(memory_id=memory_id, content=content, metadata=metadata)


def test_run_precomputes_deterministic_plan_and_stops_with_partial_progress():
    fake = FailingCrudPowerMem()
    service = LifecycleService(PowerMemClient(fake))
    memories = [
        memory_record("c", metadata_updates={"retention_score": 0.8}),
        memory_record("b", metadata_updates={"retention_score": 0.8}),
        memory_record("a", metadata_updates={"retention_score": 0.8}),
    ]

    with pytest.raises(Exception) as caught:
        service.run(memories, current_day=90)

    error = caught.value
    assert [item["memory_id"] for item in error.completed_operations] == ["a"]
    assert error.failed_operation["memory_id"] == "b"
    assert [item.memory_id for item in error.plan] == ["a", "b", "c"]
    assert [call["memory_id"] for call in fake.update_calls] == ["a"]
