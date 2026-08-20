from musicpulse.models import normalize_track, primary_genre, slug


def test_primary_genre_falls_back_to_first_tag():
    assert primary_genre({"genre": None, "tags": "rock, alternative"}) == "rock"


def test_normalize_track_adds_search_fields_and_numbers():
    result = normalize_track(
        {
            "track_id": "T1",
            "name": "  Écho ! ",
            "artist": "The Band",
            "tags": "indie, rock",
            "year": "2004",
            "energy": "0.75",
        }
    )
    assert result["year"] == 2004
    assert result["energy"] == 0.75
    assert result["primary_genre"] == "indie"
    assert result["artist_normalized"] == "the band"


def test_slug_is_search_friendly():
    assert slug("The  Killers!") == "the killers"

