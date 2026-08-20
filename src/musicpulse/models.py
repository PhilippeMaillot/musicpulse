from __future__ import annotations

import math
import re
from typing import Any, Mapping


def _clean(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def slug(value: str | None) -> str:
    value = (value or "").casefold()
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def primary_genre(row: Mapping[str, Any]) -> str:
    genre = _clean(row.get("genre"))
    if genre:
        return str(genre)
    tags = _clean(row.get("tags"))
    if tags:
        return str(tags).split(",", 1)[0].strip() or "Unknown"
    return "Unknown"


def normalize_track(row: Mapping[str, Any]) -> dict[str, Any]:
    document = {key: _clean(value) for key, value in row.items()}
    document["track_id"] = str(document.get("track_id") or "")
    document["name"] = str(document.get("name") or "Unknown track")
    document["artist"] = str(document.get("artist") or "Unknown artist")
    document["primary_genre"] = primary_genre(document)
    document["name_normalized"] = slug(document["name"])
    document["artist_normalized"] = slug(document["artist"])

    for field in ("year", "duration_ms", "key", "mode", "time_signature"):
        if document.get(field) is not None:
            document[field] = int(float(document[field]))
    for field in (
        "danceability",
        "energy",
        "loudness",
        "speechiness",
        "acousticness",
        "instrumentalness",
        "liveness",
        "valence",
        "tempo",
    ):
        if document.get(field) is not None:
            document[field] = float(document[field])
    return document

