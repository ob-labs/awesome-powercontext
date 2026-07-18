import re
from dataclasses import replace
from pathlib import Path
from threading import Event

from app.services.test_data_generator import read_memory_jsonl, write_memory_jsonl
from app.services.test_data_service import TestDataService


class RecordingMemory:
    def __init__(self, existing_rows=None):
        self.add_calls = []
        self.delete_calls = []
        self.get_all_calls = []
        self.existing_rows = existing_rows if existing_rows is not None else [
            {"id": "mem_dataset_001"},
            {"id": "mem_dataset_002"},
        ]

    def add(self, content, user_id=None, metadata=None, infer=True):
        self.add_calls.append(
            {
                "content": content,
                "user_id": user_id,
                "metadata": metadata,
                "infer": infer,
            }
        )
        return {"results": [{"id": f"mem_{len(self.add_calls)}"}]}

    def get_all(self, user_id=None, filters=None, limit=100, offset=0):
        self.get_all_calls.append(
            {"user_id": user_id, "filters": filters, "limit": limit}
        )
        return {"results": self.existing_rows[offset:offset + limit]}

    def delete(self, memory_id=None):
        self.delete_calls.append(memory_id)
        self.existing_rows = [
            row for row in self.existing_rows if str(row.get("id")) != str(memory_id)
        ]
        return True


class BlockingMemory(RecordingMemory):
    def __init__(self):
        super().__init__()
        self.started = Event()
        self.release = Event()

    def add(self, content, user_id=None, metadata=None, infer=True):
        self.started.set()
        if not self.release.wait(timeout=2):
            raise TimeoutError("blocked import was not released")
        return super().add(content, user_id=user_id, metadata=metadata, infer=infer)


class FailingMemory(RecordingMemory):
    def __init__(self):
        super().__init__(existing_rows=[])

    def add(self, content, user_id=None, metadata=None, infer=True):
        super().add(content, user_id=user_id, metadata=metadata, infer=infer)
        raise RuntimeError("Error code: 502")


class RateLimitError(RuntimeError):
    status_code = 429


class RateLimitedOnceMemory(RecordingMemory):
    def __init__(self):
        super().__init__(existing_rows=[])
        self.attempt_count = 0

    def add(self, content, user_id=None, metadata=None, infer=True):
        self.attempt_count += 1
        if self.attempt_count == 1:
            raise RateLimitError("Error code: 429")
        return super().add(content, user_id=user_id, metadata=metadata, infer=infer)


class AlwaysRateLimitedMemory(RecordingMemory):
    def __init__(self):
        super().__init__(existing_rows=[])
        self.attempt_count = 0

    def add(self, content, user_id=None, metadata=None, infer=True):
        self.attempt_count += 1
        raise RateLimitError("Error code: 429")


def assert_generated_dataset_id(
    dataset_id: str | None,
    count: int,
    seed: int,
    locale: str = "en",
) -> None:
    assert dataset_id is not None
    locale_segment = "_zh" if locale == "zh" else ""
    assert re.fullmatch(
        rf"smart_ev_cockpit_\d{{8}}_\d{{6}}_{count}_seed{seed}{locale_segment}_[0-9a-f]{{8}}",
        dataset_id,
    )


def test_generate_dataset_writes_jsonl(tmp_path: Path):
    service = TestDataService(data_root=tmp_path)

    status = service.generate_dataset(count=1000, seed=42)

    assert status.state == "generated"
    assert status.generated_count == 1000
    assert_generated_dataset_id(status.dataset_id, count=1000, seed=42)
    assert status.dataset_path is not None
    assert Path(status.dataset_path).exists()
    assert Path(status.dataset_path).name == f"{status.dataset_id}.jsonl"
    assert sum(1 for _ in Path(status.dataset_path).open()) == 1000


def test_generate_dataset_uses_distinct_paths_for_repeated_runs(tmp_path: Path):
    service = TestDataService(data_root=tmp_path)

    first = service.generate_dataset(count=3, seed=42)
    second = service.generate_dataset(count=3, seed=42)

    assert first.dataset_id != second.dataset_id
    assert first.dataset_path != second.dataset_path
    assert first.dataset_path is not None
    assert second.dataset_path is not None
    assert Path(first.dataset_path).exists()
    assert Path(second.dataset_path).exists()


def test_generate_dataset_writes_chinese_jsonl_when_locale_is_zh(tmp_path: Path):
    service = TestDataService(data_root=tmp_path)

    status = service.generate_dataset(count=4, seed=99, locale="zh")

    assert status.state == "generated"
    assert status.locale == "zh"
    assert_generated_dataset_id(status.dataset_id, count=4, seed=99, locale="zh")
    assert status.dataset_path is not None
    dataset_text = Path(status.dataset_path).read_text(encoding="utf-8")
    assert "座舱" in dataset_text


def test_import_dataset_dry_run_does_not_write(tmp_path: Path):
    service = TestDataService(data_root=tmp_path)
    generated = service.generate_dataset(count=5, seed=1)
    memory = RecordingMemory()

    status = service.import_dataset(
        memory=memory,
        dataset_id=generated.dataset_id,
        apply=False,
    )

    assert status.state == "imported"
    assert status.generated_count == 5
    assert status.imported_count == 0
    assert status.skipped_count == 5
    assert memory.add_calls == []


def test_import_dataset_apply_writes_rows_with_infer_disabled(tmp_path: Path):
    service = TestDataService(data_root=tmp_path)
    generated = service.generate_dataset(count=3, seed=2)
    memory = RecordingMemory(existing_rows=[])

    status = service.import_dataset(
        memory=memory,
        dataset_id=generated.dataset_id,
        apply=True,
    )

    assert status.state == "imported"
    assert status.imported_count == 3
    assert status.skipped_count == 0
    assert len(memory.add_calls) == 3
    assert all(call["infer"] is False for call in memory.add_calls)
    assert all(
        call["metadata"]["dataset_id"] == generated.dataset_id
        for call in memory.add_calls
    )


def test_import_dataset_collapses_legacy_static_capability_duplicates(tmp_path: Path):
    service = TestDataService(data_root=tmp_path)
    generated = service.generate_dataset(count=4, seed=2, locale="zh")
    dataset_path = Path(generated.dataset_path)
    rows = read_memory_jsonl(dataset_path)
    capability = next(
        row for row in rows
        if row.metadata["memory_kind"] == "vehicle_capability"
    )
    duplicate = replace(
        capability,
        metadata={
            **capability.metadata,
            "source_event_ids": ["gen_capability_legacy_duplicate"],
        },
    )
    write_memory_jsonl(dataset_path, [capability, duplicate])
    memory = RecordingMemory(existing_rows=[])

    status = service.import_dataset(
        memory=memory,
        dataset_id=generated.dataset_id,
        apply=True,
    )

    assert status.generated_count == 2
    assert status.imported_count == 1
    assert status.skipped_count == 1
    assert len(memory.add_calls) == 1


def test_import_dataset_skips_existing_logical_vehicle_capability(tmp_path: Path):
    service = TestDataService(data_root=tmp_path)
    generated = service.generate_dataset(count=4, seed=2)
    rows = read_memory_jsonl(Path(generated.dataset_path))
    capability = next(
        row for row in rows
        if row.metadata["memory_kind"] == "vehicle_capability"
    )

    class ExistingCapabilityMemory(RecordingMemory):
        def get_all(self, user_id=None, filters=None, limit=100, offset=0):
            self.get_all_calls.append(
                {"user_id": user_id, "filters": filters, "limit": limit}
            )
            if filters and "dataset_id" in filters:
                return {"results": []}
            return {"results": self.existing_rows[offset:offset + limit]}

    memory = ExistingCapabilityMemory(
        existing_rows=[
            {
                "id": "seed_capability",
                "memory": "Existing rest mode capability seed.",
                "metadata": {
                    **capability.metadata,
                    "dataset_id": "earlier_dataset",
                },
            }
        ]
    )

    status = service.import_dataset(
        memory=memory,
        dataset_id=generated.dataset_id,
        apply=True,
    )

    assert status.generated_count == 4
    assert status.imported_count == 3
    assert status.skipped_count == 1
    assert all(
        call["metadata"]["memory_kind"] != "vehicle_capability"
        for call in memory.add_calls
    )


def test_import_dataset_apply_uses_latest_actor_user_id_mapping(tmp_path: Path):
    service = TestDataService(data_root=tmp_path)
    generated = service.generate_dataset(
        count=4,
        seed=2,
        actor_user_ids={"driver_primary": "driver_at_generation"},
    )
    memory = RecordingMemory(existing_rows=[])

    service.import_dataset(
        memory=memory,
        dataset_id=generated.dataset_id,
        apply=True,
        actor_user_ids={"driver_primary": "driver_at_import"},
    )

    driver_calls = [
        call for call in memory.add_calls
        if call["metadata"]["actor_id"] == "driver_primary"
    ]
    non_driver_calls = [
        call for call in memory.add_calls
        if call["metadata"]["actor_id"] != "driver_primary"
    ]

    assert driver_calls
    assert all(call["user_id"] == "driver_at_import" for call in driver_calls)
    assert all(
        call["user_id"] == call["metadata"]["actor_id"]
        for call in non_driver_calls
    )


def test_import_dataset_apply_skips_when_dataset_already_exists(tmp_path: Path):
    service = TestDataService(data_root=tmp_path)
    generated = service.generate_dataset(count=3, seed=22)
    memory = RecordingMemory(existing_rows=[{"id": "existing_001"}])

    status = service.import_dataset(
        memory=memory,
        dataset_id=generated.dataset_id,
        apply=True,
    )

    assert status.state == "imported"
    assert status.generated_count == 3
    assert status.imported_count == 1
    assert status.skipped_count == 3
    assert memory.add_calls == []
    assert memory.get_all_calls == [
        {
            "user_id": None,
            "filters": {"dataset_id": generated.dataset_id},
            "limit": 10000,
        }
    ]


def test_start_import_dataset_reports_progress_while_background_import_runs(
    tmp_path: Path,
):
    service = TestDataService(data_root=tmp_path)
    generated = service.generate_dataset(count=4, seed=12)
    memory = BlockingMemory()
    memory.existing_rows = []

    status = service.start_import_dataset(
        memory=memory,
        dataset_id=generated.dataset_id,
        apply=True,
        max_workers=2,
    )

    assert status.state == "importing"
    assert status.generated_count == 4
    assert memory.started.wait(timeout=1)
    progress = service.status()
    assert progress.state == "importing"
    assert progress.imported_count == 0

    memory.release.set()
    finished = service.wait_for_current_job(timeout=3)

    assert finished.state == "imported"
    assert finished.imported_count == 4
    assert len(memory.add_calls) == 4


def test_start_import_dataset_stops_dispatching_after_a_failed_batch(tmp_path: Path):
    service = TestDataService(data_root=tmp_path)
    generated = service.generate_dataset(count=20, seed=12)
    memory = FailingMemory()

    service.start_import_dataset(
        memory=memory,
        dataset_id=generated.dataset_id,
        apply=True,
        max_workers=4,
    )
    finished = service.wait_for_current_job(timeout=3)

    assert finished.state == "failed"
    assert finished.failed_count == 4
    assert finished.skipped_count == 16
    assert finished.last_error == "Error code: 502"
    assert len(memory.add_calls) == 4


def test_import_dataset_retries_rate_limit_with_exponential_backoff(tmp_path: Path):
    sleep_calls = []
    service = TestDataService(data_root=tmp_path, retry_sleep=sleep_calls.append)
    generated = service.generate_dataset(count=1, seed=12)
    memory = RateLimitedOnceMemory()

    status = service.import_dataset(
        memory=memory,
        dataset_id=generated.dataset_id,
        apply=True,
        max_workers=1,
    )

    assert status.state == "imported"
    assert status.imported_count == 1
    assert status.failed_count == 0
    assert status.last_error is None
    assert memory.attempt_count == 2
    assert sleep_calls == [1.0]


def test_import_dataset_fails_after_rate_limit_retries_are_exhausted(tmp_path: Path):
    sleep_calls = []
    service = TestDataService(
        data_root=tmp_path,
        rate_limit_max_retries=2,
        retry_sleep=sleep_calls.append,
    )
    generated = service.generate_dataset(count=2, seed=12)
    memory = AlwaysRateLimitedMemory()

    status = service.import_dataset(
        memory=memory,
        dataset_id=generated.dataset_id,
        apply=True,
        max_workers=1,
    )

    assert status.state == "failed"
    assert status.imported_count == 0
    assert status.failed_count == 1
    assert status.skipped_count == 1
    assert status.last_error == "Error code: 429"
    assert memory.attempt_count == 3
    assert sleep_calls == [1.0, 2.0]


def test_clear_all_memories_deletes_the_entire_collection(tmp_path: Path):
    service = TestDataService(data_root=tmp_path)
    memory = RecordingMemory(
        existing_rows=[{"id": f"mem_{index:04d}"} for index in range(1001)]
    )

    status = service.clear_all_memories(memory=memory, apply=True)

    assert status.state == "deleted"
    assert status.dataset_id is None
    assert status.deleted_count == 1001
    assert status.failed_count == 0
    assert memory.existing_rows == []
    assert memory.get_all_calls == [
        {"user_id": None, "filters": None, "limit": 1000},
        {"user_id": None, "filters": None, "limit": 1000},
        {"user_id": None, "filters": None, "limit": 1000},
    ]


def test_delete_dataset_dry_run_does_not_delete(tmp_path: Path):
    service = TestDataService(data_root=tmp_path)
    generated = service.generate_dataset(count=2, seed=3)
    memory = RecordingMemory()

    status = service.delete_dataset(
        memory=memory,
        dataset_id=generated.dataset_id,
        apply=False,
    )

    assert status.state == "deleted"
    assert status.deleted_count == 0
    assert status.skipped_count == 2
    assert memory.get_all_calls == [
        {
            "user_id": None,
            "filters": {"dataset_id": generated.dataset_id},
            "limit": 10000,
        }
    ]
    assert memory.delete_calls == []


def test_delete_dataset_apply_deletes_matching_ids(tmp_path: Path):
    service = TestDataService(data_root=tmp_path)
    generated = service.generate_dataset(count=2, seed=4)
    memory = RecordingMemory()

    status = service.delete_dataset(
        memory=memory,
        dataset_id=generated.dataset_id,
        apply=True,
    )

    assert status.state == "deleted"
    assert status.deleted_count == 2
    assert status.skipped_count == 0
    assert memory.delete_calls == ["mem_dataset_001", "mem_dataset_002"]
