from __future__ import annotations

import argparse
import sys
from itertools import islice
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from musicpulse.config import settings
from musicpulse.etl import iter_tracks
from musicpulse.firestore_repository import FirestoreMusicRepository


def main() -> None:
    parser = argparse.ArgumentParser(description="Importe le catalogue dans Firestore")
    parser.add_argument("--tracks", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=0, help="0 importe tout le catalogue")
    args = parser.parse_args()
    repository = FirestoreMusicRepository(
        settings.firebase_project_id, settings.firebase_credentials
    )
    records = iter_tracks(args.tracks)
    if args.limit:
        records = islice(records, args.limit)
    count = repository.upsert_tracks(records)
    print(f"{count:,} morceaux importés dans Firestore")


if __name__ == "__main__":
    main()

