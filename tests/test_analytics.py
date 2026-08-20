import pandas as pd

from musicpulse.analytics import recommend_similar, top_tracks


def _tracks():
    return pd.DataFrame(
        [
            {"track_id": "a", "name": "A", "artist": "X", "primary_genre": "rock", "danceability": .5, "energy": .7, "speechiness": .1, "acousticness": .2, "instrumentalness": 0, "liveness": .1, "valence": .6, "tempo": 120},
            {"track_id": "b", "name": "B", "artist": "X", "primary_genre": "rock", "danceability": .51, "energy": .71, "speechiness": .1, "acousticness": .2, "instrumentalness": 0, "liveness": .1, "valence": .61, "tempo": 121},
            {"track_id": "c", "name": "C", "artist": "Y", "primary_genre": "jazz", "danceability": .1, "energy": .2, "speechiness": .4, "acousticness": .9, "instrumentalness": .8, "liveness": .5, "valence": .2, "tempo": 70},
        ]
    )


def test_top_tracks_aggregates_playcounts():
    history = pd.DataFrame([{"track_id": "a", "playcount": 2}, {"track_id": "a", "playcount": 3}, {"track_id": "b", "playcount": 1}])
    result = top_tracks(_tracks(), history, 1)
    assert result.iloc[0]["track_id"] == "a"
    assert result.iloc[0]["playcount"] == 5


def test_recommend_similar_excludes_source_and_finds_neighbour():
    result = recommend_similar(_tracks(), "a", 1)
    assert result.iloc[0]["track_id"] == "b"

