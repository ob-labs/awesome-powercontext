import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from powermem import create_memory  # noqa: E402

from app.services.test_data_service import TestDataService  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Delete a generated test dataset.")
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    memory = create_memory()
    status = TestDataService().delete_dataset(
        memory=memory,
        dataset_id=args.dataset_id,
        apply=args.apply,
    )
    print(status.model_dump())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
