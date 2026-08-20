from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from musicpulse.config import settings
from musicpulse.redis_service import RedisMusicService


def main() -> None:
    parser = argparse.ArgumentParser(description="Alimente les classements Redis")
    parser.add_argument("--tracks", type=Path, required=True)
    parser.add_argument("--history", type=Path, required=True)
    args = parser.parse_args()

    tracks = pd.read_csv(args.tracks, usecols=["track_id", "artist"])
    artists = tracks.set_index("track_id")["artist"].to_dict()
    totals: dict[str, int] = {}
    for chunk in pd.read_csv(args.history, chunksize=500_000):
        grouped = chunk.groupby("track_id")["playcount"].sum()
        for track_id, count in grouped.items():
            totals[str(track_id)] = totals.get(str(track_id), 0) + int(count)

    service = RedisMusicService(settings.redis_url, settings.cache_ttl_seconds)
    pipeline = service.client.pipeline(transaction=False)
    for index, (track_id, count) in enumerate(totals.items(), start=1):
        pipeline.zadd("ranking:tracks:global", {track_id: count})
        artist = artists.get(track_id)
        if artist:
            pipeline.zincrby("ranking:artists:global", count, artist)
        if index % 5_000 == 0:
            pipeline.execute()
    pipeline.execute()
    print(f"Classements Redis alimentés avec {len(totals):,} morceaux")


if __name__ == "__main__":
    main()

