from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Literal

from app.domain.memory_models import MemoryRecord
from app.powermem.client import PowerMemClient
from app.services.memory_service import MemoryService

SCENARIO_START_DATE = date(2026, 1, 1)


@dataclass(frozen=True)
class LifecycleOperation:
    type: Literal["UPDATE", "DELETE"]
    memory_id: str
    before_status: str
    after_status: str
    memory: MemoryRecord = field(repr=False)
    metadata_updates: dict = field(default_factory=dict, repr=False)


@dataclass
class LifecycleRunResult:
    plan: list[LifecycleOperation]
    completed_operations: list[dict]
    failed_operation: dict | None
    audit: list[dict]


class LifecycleExecutionError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        plan: list[LifecycleOperation],
        completed_operations: list[dict],
        failed_operation: dict,
        audit: list[dict],
        memories: list[MemoryRecord] | None = None,
    ):
        super().__init__(message)
        self.plan = plan
        self.completed_operations = completed_operations
        self.failed_operation = failed_operation
        self.audit = audit
        self.trace_id: str | None = None
        self.memories: list[MemoryRecord] = memories or []


class LifecycleService:
    def __init__(self, client: PowerMemClient | None = None):
        self._memory_service = MemoryService(client) if client is not None else None

    def apply_clock(self, memory: MemoryRecord, current_day: int) -> MemoryRecord:
        if memory.metadata.memory_kind == "temporary_context" and current_day >= 90:
            metadata = memory.metadata.model_copy(
                update={"lifecycle_status": "decayed", "retention_score": 0.18}
            )
            return memory.model_copy(update={"metadata": metadata})
        return memory

    def plan(
        self,
        memories: list[MemoryRecord],
        current_day: int,
    ) -> list[LifecycleOperation]:
        operations: list[LifecycleOperation] = []
        if current_day < 90:
            return operations
        for memory in sorted(memories, key=lambda item: item.memory_id):
            metadata = memory.metadata
            if metadata.memory_kind != "temporary_context":
                continue
            if metadata.retention_policy == "expire_after_valid_until":
                if self._is_expired(metadata.valid_until, current_day):
                    operations.append(
                        LifecycleOperation(
                            type="DELETE",
                            memory_id=memory.memory_id,
                            before_status=metadata.lifecycle_status,
                            after_status="deleted",
                            memory=memory,
                        )
                    )
                continue
            if metadata.lifecycle_status == "archived":
                continue
            should_archive = (
                metadata.lifecycle_status == "decayed" or metadata.retention_score <= 0.25
            )
            after_status = "archived" if should_archive else "decayed"
            updates = {"lifecycle_status": after_status}
            if after_status == "decayed":
                updates["retention_score"] = 0.18
            if not memory.content.strip():
                continue
            operations.append(
                LifecycleOperation(
                    type="UPDATE",
                    memory_id=memory.memory_id,
                    before_status=metadata.lifecycle_status,
                    after_status=after_status,
                    memory=memory,
                    metadata_updates=updates,
                )
            )
        return operations

    def run(
        self,
        memories: list[MemoryRecord],
        current_day: int,
    ) -> LifecycleRunResult:
        if self._memory_service is None:
            raise RuntimeError("Lifecycle execution requires a PowerMem client")
        plan = self.plan(memories, current_day)
        completed: list[dict] = []
        audit = self._skipped_update_evidence(memories, current_day)
        for operation in plan:
            evidence = self._operation_evidence(operation)
            try:
                if operation.type == "UPDATE":
                    update_result = self._memory_service.update(
                        operation.memory,
                        operation.metadata_updates,
                    )
                    if not self._is_successful_update(update_result):
                        raise RuntimeError("PowerMem did not confirm update")
                else:
                    deleted = self._memory_service.delete(operation.memory_id)
                    if not deleted:
                        raise RuntimeError("PowerMem did not confirm deletion")
            except Exception as exc:
                failed = {**evidence, "result": "failed", "error": str(exc)}
                audit.append(failed)
                raise LifecycleExecutionError(
                    f"Lifecycle operation failed for {operation.memory_id}",
                    plan=plan,
                    completed_operations=completed,
                    failed_operation=failed,
                    audit=audit,
                    memories=[],
                ) from exc
            succeeded = {**evidence, "result": "ok"}
            completed.append(succeeded)
            audit.append(succeeded)
        return LifecycleRunResult(
            plan=plan,
            completed_operations=completed,
            failed_operation=None,
            audit=audit,
        )

    @staticmethod
    def _is_expired(valid_until: str | None, current_day: int) -> bool:
        if valid_until is None:
            return False
        try:
            expiry = date.fromisoformat(valid_until)
        except ValueError:
            try:
                expiry = datetime.fromisoformat(valid_until).date()
            except ValueError:
                return False
        scenario_date = SCENARIO_START_DATE + timedelta(days=current_day - 1)
        return scenario_date > expiry

    @staticmethod
    def _is_successful_update(result: object) -> bool:
        if result is True:
            return True
        if not isinstance(result, dict) or not result or "error" in result:
            return False
        if "success" in result:
            return result["success"] is True
        return True

    def _skipped_update_evidence(
        self,
        memories: list[MemoryRecord],
        current_day: int,
    ) -> list[dict]:
        if current_day < 90:
            return []
        skipped = []
        for memory in sorted(memories, key=lambda item: item.memory_id):
            metadata = memory.metadata
            if (
                metadata.memory_kind != "temporary_context"
                or metadata.retention_policy == "expire_after_valid_until"
                or metadata.lifecycle_status == "archived"
                or memory.content.strip()
            ):
                continue
            after_status = (
                "archived"
                if metadata.lifecycle_status == "decayed"
                or metadata.retention_score <= 0.25
                else "decayed"
            )
            skipped.append(
                {
                    "type": "UPDATE",
                    "memory_id": memory.memory_id,
                    "memory_ids": [memory.memory_id],
                    "before_status": metadata.lifecycle_status,
                    "after_status": after_status,
                    "result": "skipped",
                    "reason": "empty_content",
                }
            )
        return skipped

    @staticmethod
    def _operation_evidence(operation: LifecycleOperation) -> dict:
        return {
            "type": operation.type,
            "memory_id": operation.memory_id,
            "memory_ids": [operation.memory_id],
            "before_status": operation.before_status,
            "after_status": operation.after_status,
        }
