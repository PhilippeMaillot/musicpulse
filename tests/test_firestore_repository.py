import pytest

from musicpulse.firestore_repository import FirestoreMusicRepository


class FakeSnapshot:
    def __init__(self, data):
        self._data = data
        self.exists = data is not None

    def to_dict(self):
        return dict(self._data)


class FakeReference:
    def __init__(self, data):
        self.snapshot = FakeSnapshot(data)
        self.updated = None

    def get(self):
        return self.snapshot

    def update(self, changes):
        self.updated = changes


class FakeCollection:
    def __init__(self, reference):
        self.reference = reference

    def document(self, _track_id):
        return self.reference


class FakeClient:
    def __init__(self, reference):
        self.reference = reference

    def collection(self, _name):
        return FakeCollection(self.reference)


def repository_with(data):
    repository = object.__new__(FirestoreMusicRepository)
    reference = FakeReference(data)
    repository.client = FakeClient(reference)
    return repository, reference


def test_update_track_recomputes_denormalized_fields():
    repository, reference = repository_with(
        {
            "track_id": "T1",
            "name": "Ancien titre",
            "artist": "Ancien artiste",
            "genre": "rock",
            "year": 2000,
        }
    )

    repository.update_track(
        "T1", {"name": "Nouveau titre", "artist": "Nouvel artiste", "genre": "jazz"}
    )

    assert reference.updated["name"] == "Nouveau titre"
    assert reference.updated["name_normalized"] == "nouveau titre"
    assert reference.updated["artist_normalized"] == "nouvel artiste"
    assert reference.updated["primary_genre"] == "jazz"
    assert "track_id" not in reference.updated


def test_update_track_rejects_unknown_track():
    repository, _ = repository_with(None)

    with pytest.raises(ValueError, match="n'existe pas"):
        repository.update_track("UNKNOWN", {"name": "Titre"})
