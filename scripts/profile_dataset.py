from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from musicpulse.etl import profile_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Profile les deux fichiers Kaggle MusicPulse")
    parser.add_argument("--tracks", type=Path, required=True)
    parser.add_argument("--history", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(profile_dataset(args.tracks, args.history), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

