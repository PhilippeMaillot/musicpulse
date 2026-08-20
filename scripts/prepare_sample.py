from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from musicpulse.etl import build_sample


def main() -> None:
    parser = argparse.ArgumentParser(description="Construit un échantillon reproductible")
    parser.add_argument("--tracks", type=Path, required=True)
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "sample")
    parser.add_argument("--track-limit", type=int, default=2_000)
    parser.add_argument("--interaction-limit", type=int, default=100_000)
    args = parser.parse_args()
    tracks, interactions = build_sample(
        args.tracks,
        args.history,
        args.output,
        args.track_limit,
        args.interaction_limit,
    )
    print(f"Échantillon créé : {tracks:,} morceaux, {interactions:,} interactions")


if __name__ == "__main__":
    main()

