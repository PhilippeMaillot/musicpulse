from __future__ import annotations

import json
from typing import Any


class RedisMusicService:
    def __init__(self, redis_url: str, cache_ttl_seconds: int = 900) -> None:
        try:
            import redis
        except ImportError as exc:
            raise RuntimeError("Le paquet redis n'est pas installé.") from exc
        self.client = redis.Redis.from_url(redis_url, decode_responses=True)
        self.cache_ttl_seconds = cache_ttl_seconds

    def ping(self) -> bool:
        return bool(self.client.ping())

    def cache_track(self, track_id: str, track: dict[str, Any]) -> None:
        """Place une fiche morceau dans un cache String avec expiration."""
        self.client.setex(
            f"track:{track_id}:cache",
            self.cache_ttl_seconds,
            json.dumps(track, ensure_ascii=False, default=str),
        )

    def get_cached_track(self, track_id: str) -> dict[str, Any] | None:
        """Retourne la fiche en cache, ou None pour matérialiser un cache miss."""
        value = self.client.get(f"track:{track_id}:cache")
        return json.loads(value) if value else None

    def invalidate_track_cache(self, track_id: str) -> int:
        return int(self.client.delete(f"track:{track_id}:cache"))

    def track_cache_ttl(self, track_id: str) -> int:
        return int(self.client.ttl(f"track:{track_id}:cache"))

    def record_listen(
        self, user_id: str, track_id: str, artist: str, count: int = 1
    ) -> None:
        pipeline = self.client.pipeline(transaction=True)
        pipeline.zincrby("ranking:tracks:global", count, track_id)
        pipeline.zincrby("ranking:artists:global", count, artist)
        pipeline.lpush(f"user:{user_id}:recent_tracks", track_id)
        pipeline.ltrim(f"user:{user_id}:recent_tracks", 0, 49)
        pipeline.hincrby(f"track:{track_id}:stats", "playcount", count)
        pipeline.execute()

    def top_tracks(self, limit: int = 10) -> list[tuple[str, float]]:
        return self.client.zrevrange(
            "ranking:tracks:global", 0, limit - 1, withscores=True
        )

    def track_stats(self, track_id: str) -> dict[str, str]:
        return self.client.hgetall(f"track:{track_id}:stats")

    def recent_tracks(self, user_id: str, limit: int = 10) -> list[str]:
        return self.client.lrange(f"user:{user_id}:recent_tracks", 0, limit - 1)

    def cache_recommendations(
        self, user_id: str, recommendations: list[dict[str, Any]]
    ) -> None:
        self.client.setex(
            f"recommendations:user:{user_id}",
            self.cache_ttl_seconds,
            json.dumps(recommendations, ensure_ascii=False),
        )

    def get_recommendations(self, user_id: str) -> list[dict[str, Any]] | None:
        value = self.client.get(f"recommendations:user:{user_id}")
        return json.loads(value) if value else None
