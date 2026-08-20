from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # Le mode démo reste importable avant l'installation.
    def load_dotenv(*_args, **_kwargs):
        return False


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    mode: str = os.getenv("MUSICPULSE_MODE", "demo")
    redis_url: str = os.getenv("MUSICPULSE_REDIS_URL", "redis://localhost:6379/0")
    firebase_project_id: str = os.getenv(
        "MUSICPULSE_FIREBASE_PROJECT_ID", "musicpulse-demo"
    )
    firebase_credentials: Path = PROJECT_ROOT / os.getenv(
        "MUSICPULSE_FIREBASE_CREDENTIALS", "firebase-service-account.json"
    )
    data_dir: Path = PROJECT_ROOT / os.getenv(
        "MUSICPULSE_DATA_DIR", "data/sample"
    )
    cache_ttl_seconds: int = int(
        os.getenv("MUSICPULSE_CACHE_TTL_SECONDS", "900")
    )

    @property
    def connected(self) -> bool:
        return self.mode.lower() == "connected"


settings = Settings()
