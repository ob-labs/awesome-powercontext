import argparse
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.test_data_service import TestDataService  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate smart EV cockpit test data.")
    parser.add_argument("--count", type=int, default=1200)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    status = TestDataService().generate_dataset(count=args.count, seed=args.seed)
    print(status.model_dump())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
