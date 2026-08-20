from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .models import primary_genre


AUDIO_FEATURES = [
    "danceability",
    "energy",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
]


def load_demo_data(data_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    tracks = pd.read_csv(data_dir / "tracks_sample.csv")
    history = pd.read_csv(data_dir / "listening_history_sample.csv")
    tracks["primary_genre"] = tracks.apply(primary_genre, axis=1)
    return tracks, history


def enriched_history(
    tracks: pd.DataFrame, history: pd.DataFrame
) -> pd.DataFrame:
    columns = ["track_id", "name", "artist", "primary_genre"]
    return history.merge(tracks[columns], on="track_id", how="left")


def top_tracks(
    tracks: pd.DataFrame, history: pd.DataFrame, limit: int = 10
) -> pd.DataFrame:
    totals = (
        history.groupby("track_id", as_index=False)["playcount"]
        .sum()
        .sort_values("playcount", ascending=False)
        .head(limit)
    )
    return totals.merge(
        tracks[["track_id", "name", "artist", "primary_genre"]],
        on="track_id",
        how="left",
    )


def top_artists(
    tracks: pd.DataFrame, history: pd.DataFrame, limit: int = 10
) -> pd.DataFrame:
    enriched = enriched_history(tracks, history)
    return (
        enriched.groupby("artist", as_index=False)["playcount"]
        .sum()
        .sort_values("playcount", ascending=False)
        .head(limit)
    )


def genre_distribution(
    tracks: pd.DataFrame, history: pd.DataFrame, limit: int = 12
) -> pd.DataFrame:
    enriched = enriched_history(tracks, history)
    return (
        enriched.groupby("primary_genre", as_index=False)["playcount"]
        .sum()
        .sort_values("playcount", ascending=False)
        .head(limit)
    )


def recommend_similar(
    tracks: pd.DataFrame, track_id: str, limit: int = 8
) -> pd.DataFrame:
    available = [column for column in AUDIO_FEATURES if column in tracks.columns]
    frame = tracks.dropna(subset=available).copy()
    if track_id not in set(frame["track_id"]):
        return frame.head(0)

    matrix = frame[available].astype(float).to_numpy()
    means = matrix.mean(axis=0)
    scales = matrix.std(axis=0)
    scales[scales == 0] = 1
    normalized = (matrix - means) / scales
    target_index = frame.index.get_loc(frame.index[frame["track_id"] == track_id][0])
    distances = np.linalg.norm(normalized - normalized[target_index], axis=1)
    frame["distance"] = distances
    columns = [
        "track_id",
        "name",
        "artist",
        "primary_genre",
        "energy",
        "danceability",
        "valence",
        "distance",
    ]
    return frame[frame["track_id"] != track_id].nsmallest(limit, "distance")[columns]

