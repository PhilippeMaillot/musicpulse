from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .models import normalize_track


class FirestoreMusicRepository:
    def __init__(self, project_id: str, credentials_path: Path | None = None) -> None:
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
        except ImportError as exc:
            raise RuntimeError("Le paquet firebase-admin n'est pas installé.") from exc

        if not firebase_admin._apps:
            options = {"projectId": project_id}
            if credentials_path and credentials_path.exists():
                firebase_admin.initialize_app(
                    credentials.Certificate(str(credentials_path)), options
                )
            else:
                firebase_admin.initialize_app(options=options)
        self.client = firestore.client()

    def create_track(self, track: dict[str, Any]) -> dict[str, Any]:
        document = normalize_track(track)
        if not document["track_id"]:
            raise ValueError("track_id est obligatoire")
        reference = self.client.collection("tracks").document(document["track_id"])
        if reference.get().exists:
            raise ValueError(f"Le morceau {document['track_id']} existe déjà")
        reference.set(document)
        return document

    def get_track(self, track_id: str) -> dict[str, Any] | None:
        snapshot = self.client.collection("tracks").document(track_id).get()
        return snapshot.to_dict() if snapshot.exists else None

    def update_track(self, track_id: str, changes: dict[str, Any]) -> None:
        forbidden = {"track_id"}
        cleaned = {key: value for key, value in changes.items() if key not in forbidden}
        self.client.collection("tracks").document(track_id).update(cleaned)

    def delete_track(self, track_id: str) -> None:
        self.client.collection("tracks").document(track_id).delete()

    def upsert_tracks(self, tracks: Iterable[dict[str, Any]], batch_size: int = 400) -> int:
        count = 0
        batch = self.client.batch()
        for track in tracks:
            document = normalize_track(track)
            reference = self.client.collection("tracks").document(document["track_id"])
            batch.set(reference, document, merge=True)
            count += 1
            if count % batch_size == 0:
                batch.commit()
                batch = self.client.batch()
        if count % batch_size:
            batch.commit()
        return count

