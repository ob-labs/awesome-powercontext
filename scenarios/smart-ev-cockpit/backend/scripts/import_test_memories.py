import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from powermem import create_memory  # noqa: E402

from app.services.test_data_service import TestDataService  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Import generated test memories.")
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--max-workers", type=int, default=8)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    memory = create_memory()
    status = TestDataService().import_dataset(
        memory=memory,
        dataset_id=args.dataset_id,
        apply=args.apply,
        limit=args.limit,
        max_workers=args.max_workers,
    )
    print(status.model_dump())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
