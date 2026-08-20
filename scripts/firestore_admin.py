from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from musicpulse.config import settings
from musicpulse.firestore_repository import FirestoreMusicRepository


def backup(collection: str, output: Path) -> None:
    repository = FirestoreMusicRepository(
        settings.firebase_project_id, settings.firebase_credentials
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as stream:
        for snapshot in repository.client.collection(collection).stream():
            payload = {"id": snapshot.id, "data": snapshot.to_dict()}
            stream.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")


def restore(collection: str, source: Path) -> None:
    repository = FirestoreMusicRepository(
        settings.firebase_project_id, settings.firebase_credentials
    )
    batch = repository.client.batch()
    count = 0
    with source.open("r", encoding="utf-8") as stream:
        for line in stream:
            payload = json.loads(line)
            reference = repository.client.collection(collection).document(payload["id"])
            batch.set(reference, payload["data"], merge=True)
            count += 1
            if count % 400 == 0:
                batch.commit()
                batch = repository.client.batch()
    if count % 400:
        batch.commit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Sauvegarde/restauration Firestore JSONL")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("backup", "restore"):
        sub = subparsers.add_parser(command)
        sub.add_argument("--collection", default="tracks")
        sub.add_argument("--file", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "backup":
        backup(args.collection, args.file)
    else:
        restore(args.collection, args.file)


if __name__ == "__main__":
    main()

