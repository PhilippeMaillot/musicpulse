from __future__ import annotations

import csv
import heapq
from collections import Counter
from pathlib import Path
from typing import Iterator

import pandas as pd

from .models import normalize_track


def iter_tracks(path: Path) -> Iterator[dict]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as stream:
        for row in csv.DictReader(stream):
            yield normalize_track(row)


def profile_dataset(tracks_path: Path, history_path: Path) -> dict:
    tracks = pd.read_csv(tracks_path)
    users: set[str] = set()
    listened_tracks: set[str] = set()
    history_rows = 0
    total_plays = 0
    max_playcount = 0
    for chunk in pd.read_csv(history_path, chunksize=500_000):
        history_rows += len(chunk)
        total_plays += int(chunk["playcount"].sum())
        max_playcount = max(max_playcount, int(chunk["playcount"].max()))
        users.update(chunk["user_id"].unique())
        listened_tracks.update(chunk["track_id"].unique())
    return {
        "tracks": len(tracks),
        "unique_tracks": int(tracks["track_id"].nunique()),
        "artists": int(tracks["artist"].nunique()),
        "history_rows": history_rows,
        "users": len(users),
        "listened_tracks": len(listened_tracks),
        "total_plays": total_plays,
        "max_playcount": max_playcount,
        "missing_percent": (tracks.isna().mean() * 100).round(2).to_dict(),
    }


def build_sample(
    tracks_path: Path,
    history_path: Path,
    output_dir: Path,
    track_limit: int = 2_000,
    interaction_limit: int = 100_000,
) -> tuple[int, int]:
    playcounts: Counter[str] = Counter()
    for chunk in pd.read_csv(history_path, chunksize=500_000):
        totals = chunk.groupby("track_id")["playcount"].sum()
        playcounts.update({str(key): int(value) for key, value in totals.items()})

    selected = {
        track_id for track_id, _ in heapq.nlargest(track_limit, playcounts.items(), key=lambda x: x[1])
    }
    tracks = pd.read_csv(tracks_path)
    tracks_sample = tracks[tracks["track_id"].isin(selected)].copy()

    history_parts: list[pd.DataFrame] = []
    remaining = interaction_limit
    for chunk in pd.read_csv(history_path, chunksize=500_000):
        filtered = chunk[chunk["track_id"].isin(selected)]
        if not filtered.empty:
            take = filtered.head(remaining)
            history_parts.append(take)
            remaining -= len(take)
        if remaining <= 0:
            break
    history_sample = pd.concat(history_parts, ignore_index=True)

    output_dir.mkdir(parents=True, exist_ok=True)
    tracks_sample.to_csv(output_dir / "tracks_sample.csv", index=False)
    history_sample.to_csv(output_dir / "listening_history_sample.csv", index=False)
    return len(tracks_sample), len(history_sample)

