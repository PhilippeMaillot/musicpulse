from __future__ import annotations

import sys
from pathlib import Path
from time import perf_counter

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from musicpulse.analytics import (
    genre_distribution,
    load_demo_data,
    recommend_similar,
    top_artists,
    top_tracks,
)
from musicpulse.config import settings
from musicpulse.firestore_repository import FirestoreMusicRepository
from musicpulse.redis_service import RedisMusicService


st.set_page_config(page_title="MusicPulse", page_icon="🎧", layout="wide")
st.markdown(
    """
    <style>
      .block-container {padding-top: 2rem; max-width: 1280px;}
      [data-testid="stMetric"] {background:#151821; border:1px solid #292d3a; padding:16px; border-radius:14px;}
      h1, h2, h3 {letter-spacing:-0.02em;}
      .hero {padding:26px 30px; border-radius:20px; background:linear-gradient(120deg,#4424a7,#ba247f); margin-bottom:20px;}
      .hero p {margin:0; color:#f4eefe;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def demo_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    return load_demo_data(settings.data_dir)


@st.cache_resource
def connected_services() -> tuple[FirestoreMusicRepository, RedisMusicService]:
    """Connexions réutilisées par les actions de la démonstration live."""
    repository = FirestoreMusicRepository(
        settings.firebase_project_id, settings.firebase_credentials
    )
    redis_service = RedisMusicService(
        settings.redis_url, settings.cache_ttl_seconds
    )
    return repository, redis_service


tracks, history = demo_data()

st.markdown(
    """
    <div class="hero">
      <h1>MusicPulse</h1>
      <p>Démontrer comment Firestore et Redis se complètent dans une application musicale.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

dashboard, explorer, recommendations, admin, live_demo, architecture = st.tabs(
    [
        "Vue d’ensemble",
        "Explorer",
        "Cas d’usage",
        "CRUD Firestore",
        "Démo live",
        "Firebase & Redis",
    ]
)

with dashboard:
    metric_cols = st.columns(4)
    metric_cols[0].metric("Morceaux dans la démo", f"{tracks['track_id'].nunique():,}".replace(",", " "))
    metric_cols[1].metric("Interactions", f"{len(history):,}".replace(",", " "))
    metric_cols[2].metric("Utilisateurs", f"{history['user_id'].nunique():,}".replace(",", " "))
    metric_cols[3].metric("Écoutes cumulées", f"{int(history['playcount'].sum()):,}".replace(",", " "))

    left, right = st.columns(2)
    with left:
        st.subheader("Morceaux les plus écoutés")
        top = top_tracks(tracks, history, 12)
        st.plotly_chart(
            px.bar(top.sort_values("playcount"), x="playcount", y="name", orientation="h", color="primary_genre"),
            width="stretch",
        )
    with right:
        st.subheader("Genres dominants")
        genres = genre_distribution(tracks, history)
        st.plotly_chart(
            px.treemap(genres, path=["primary_genre"], values="playcount", color="playcount"),
            width="stretch",
        )

    st.subheader("Artistes les plus écoutés")
    artists = top_artists(tracks, history, 15)
    st.plotly_chart(px.bar(artists, x="artist", y="playcount", color="playcount"), width="stretch")

with explorer:
    query = st.text_input("Rechercher un morceau ou un artiste", placeholder="Ex. Radiohead")
    genre_options = ["Tous"] + sorted(tracks["primary_genre"].dropna().unique().tolist())
    selected_genre = st.selectbox("Genre", genre_options)
    filtered = tracks.copy()
    if query:
        mask = filtered["name"].str.contains(query, case=False, na=False) | filtered["artist"].str.contains(query, case=False, na=False)
        filtered = filtered[mask]
    if selected_genre != "Tous":
        filtered = filtered[filtered["primary_genre"] == selected_genre]
    st.caption(f"{len(filtered):,} résultat(s)".replace(",", " "))
    st.dataframe(
        filtered[["name", "artist", "primary_genre", "year", "energy", "danceability", "valence"]].head(200),
        width="stretch",
        hide_index=True,
    )

with recommendations:
    st.subheader("Cas d’usage : recommandation musicale")
    st.info("Cette fonctionnalité illustre l'utilisation des données. L'objectif principal du TP reste l'explication de Firestore et Redis.")
    labels = (tracks["name"].fillna("Sans titre") + " — " + tracks["artist"].fillna("Artiste inconnu"))
    selected_label = st.selectbox("Choisir un morceau de départ", labels.tolist())
    selected_index = labels[labels == selected_label].index[0]
    selected_track = tracks.loc[selected_index]
    result = recommend_similar(tracks, str(selected_track["track_id"]))
    st.caption("Similarité calculée à partir de l’énergie, du tempo, de la danceabilité, de la valence et d’autres caractéristiques audio.")
    st.dataframe(
        result[["name", "artist", "primary_genre", "energy", "danceability", "valence", "distance"]],
        width="stretch",
        hide_index=True,
    )

with admin:
    st.subheader("CRUD du catalogue dans Firestore")
    st.caption("Create, Read, Update et Delete portent sur la source de vérité durable. Après une modification, le cache Redis associé doit être invalidé.")
    if not settings.connected:
        st.info("Mode démonstration : passez MUSICPULSE_MODE à connected pour écrire dans Firestore.")
    with st.form("create_track"):
        track_id = st.text_input("Identifiant du morceau")
        name = st.text_input("Titre")
        artist = st.text_input("Artiste")
        genre = st.text_input("Genre")
        year = st.number_input("Année", min_value=1900, max_value=2100, value=2024)
        submitted = st.form_submit_button("Ajouter dans Firestore", disabled=not settings.connected)
        if submitted:
            try:
                repository = FirestoreMusicRepository(settings.firebase_project_id, settings.firebase_credentials)
                repository.create_track({"track_id": track_id, "name": name, "artist": artist, "genre": genre, "year": year})
                st.success("Morceau ajouté.")
            except Exception as exc:
                st.error(str(exc))

    delete_id = st.text_input("Identifiant à supprimer")
    if st.button("Supprimer", disabled=not settings.connected, type="secondary"):
        try:
            repository = FirestoreMusicRepository(settings.firebase_project_id, settings.firebase_credentials)
            repository.delete_track(delete_id)
            redis_service = RedisMusicService(
                settings.redis_url, settings.cache_ttl_seconds
            )
            redis_service.invalidate_track_cache(delete_id)
            st.success("Morceau supprimé.")
        except Exception as exc:
            st.error(str(exc))

with live_demo:
    st.subheader("Démonstration live : Firestore + Redis")
    st.caption(
        "Les boutons ci-dessous matérialisent le cache-aside, le TTL, les "
        "compteurs atomiques, les Lists et les Sorted Sets."
    )

    if not settings.connected:
        st.warning(
            "Cette démonstration nécessite MUSICPULSE_MODE=connected, "
            "Firestore et Redis."
        )

    default_track_id = str(tracks.iloc[0]["track_id"]) if not tracks.empty else ""
    live_track_id = st.text_input(
        "Identifiant du morceau à démontrer",
        value=default_track_id,
        key="live_track_id",
    ).strip()

    st.markdown("#### 1. Cache-aside")
    st.write(
        "Videz le cache, cliquez une première fois sur **Lire le morceau** "
        "pour provoquer un MISS, puis une seconde fois pour obtenir un HIT."
    )
    cache_clear_col, cache_read_col, ttl_col = st.columns([1, 1.4, 1])

    with cache_clear_col:
        clear_cache = st.button(
            "1 — Vider le cache",
            disabled=not settings.connected or not live_track_id,
            width="stretch",
        )
    with cache_read_col:
        read_track = st.button(
            "2 — Lire le morceau",
            disabled=not settings.connected or not live_track_id,
            type="primary",
            width="stretch",
        )
    with ttl_col:
        st.button(
            "3 — Actualiser le TTL",
            disabled=not settings.connected or not live_track_id,
            width="stretch",
            help="Relance l’affichage pour constater que le TTL diminue.",
        )

    if clear_cache:
        try:
            _, redis_service = connected_services()
            deleted = redis_service.invalidate_track_cache(live_track_id)
            st.session_state.pop("live_cache_result", None)
            st.success(
                "Cache vidé : la prochaine lecture sera un MISS."
                if deleted
                else "La clé était déjà absente : la prochaine lecture sera un MISS."
            )
        except Exception as exc:
            st.error(f"Impossible de vider le cache : {exc}")

    if read_track:
        try:
            repository, redis_service = connected_services()
            started = perf_counter()
            document = redis_service.get_cached_track(live_track_id)
            source = "Redis — CACHE HIT"
            if document is None:
                source = "Firestore — CACHE MISS"
                document = repository.get_track(live_track_id)
                if document is not None:
                    redis_service.cache_track(live_track_id, document)
            elapsed_ms = (perf_counter() - started) * 1000
            st.session_state["live_cache_result"] = {
                "track_id": live_track_id,
                "source": source,
                "elapsed_ms": elapsed_ms,
                "document": document,
            }
        except Exception as exc:
            st.error(f"Lecture impossible : {exc}")

    cache_result = st.session_state.get("live_cache_result")
    if cache_result and cache_result.get("track_id") == live_track_id:
        if cache_result["document"] is None:
            st.warning("Ce morceau n’existe pas dans Firestore.")
        else:
            source_col, time_col, current_ttl_col = st.columns(3)
            source_col.metric("Source de la lecture", cache_result["source"])
            time_col.metric(
                "Temps mesuré", f"{cache_result['elapsed_ms']:.2f} ms"
            )
            try:
                _, redis_service = connected_services()
                current_ttl = redis_service.track_cache_ttl(live_track_id)
            except Exception:
                current_ttl = -2
            current_ttl_col.metric(
                "TTL Redis",
                f"{current_ttl} s" if current_ttl >= 0 else "clé absente",
            )
            st.json(cache_result["document"])
    st.divider()
    st.markdown("#### 2. Simulation d’écoutes")
    listen_left, listen_middle, listen_right = st.columns([1.3, 1, 1.2])
    with listen_left:
        live_user_id = st.text_input(
            "Utilisateur de démonstration", value="demo", key="live_user_id"
        ).strip()
    with listen_middle:
        listen_count = st.number_input(
            "Nombre d’écoutes",
            min_value=1,
            max_value=100,
            value=5,
            step=1,
        )
    with listen_right:
        st.write("")
        st.write("")
        simulate_listens = st.button(
            "Simuler les écoutes",
            disabled=(
                not settings.connected or not live_track_id or not live_user_id
            ),
            type="primary",
            width="stretch",
        )

    if simulate_listens:
        try:
            repository, redis_service = connected_services()
            document = repository.get_track(live_track_id)
            if document is None:
                st.error("Le morceau n’existe pas dans Firestore.")
            else:
                redis_service.record_listen(
                    live_user_id,
                    live_track_id,
                    str(document.get("artist") or "Artiste inconnu"),
                    int(listen_count),
                )
                st.session_state["live_listen_result"] = {
                    "track_id": live_track_id,
                    "user_id": live_user_id,
                    "count": int(listen_count),
                }
                st.success(f"{int(listen_count)} écoute(s) ajoutée(s) dans Redis.")
        except Exception as exc:
            st.error(f"Simulation impossible : {exc}")

    listen_result = st.session_state.get("live_listen_result")
    if listen_result:
        try:
            _, redis_service = connected_services()
            stats = redis_service.track_stats(live_track_id)
            recent = redis_service.recent_tracks(live_user_id, 10)
            ranking = redis_service.top_tracks(10)

            stats_col, recent_col = st.columns(2)
            with stats_col:
                st.markdown("**Hash — compteur du morceau**")
                st.code(
                    f"track:{live_track_id}:stats\n"
                    f"playcount = {stats.get('playcount', '0')}",
                    language="text",
                )
            with recent_col:
                st.markdown("**List — dernières écoutes**")
                st.code(
                    "\n".join(recent) if recent else "Liste vide", language="text"
                )

            st.markdown("**Sorted Set — classement global Redis**")
            ranking_frame = pd.DataFrame(ranking, columns=["track_id", "score"])
            ranking_frame.index = ranking_frame.index + 1
            st.dataframe(ranking_frame, width="stretch")
        except Exception as exc:
            st.error(f"Lecture des structures Redis impossible : {exc}")

with architecture:
    st.subheader("Pourquoi combiner Firebase et Redis ?")
    st.markdown(
        """
        **Cloud Firestore — source de vérité durable**

        - catalogue des morceaux et artistes ;
        - profils, playlists et favoris ;
        - recommandations et agrégats persistants ;
        - collections, documents dénormalisés et index composés ;
        - contrôle des accès avec Firebase Authentication et les règles de sécurité.

        **Redis — couche rapide et temporaire**

        - `Sorted Set` pour les classements globaux et quotidiens ;
        - `List` pour les dernières écoutes et files d'attente ;
        - `Hash` et incréments atomiques pour les compteurs ;
        - `String` JSON pour le cache avec expiration TTL.

        **Scénario cache-aside**

        1. l'application cherche la fiche dans Redis ;
        2. si la clé est absente, elle lit Firestore ;
        3. le document est placé dans Redis avec un TTL ;
        4. la lecture suivante est servie directement depuis Redis ;
        5. une modification Firestore invalide la clé concernée.

        Le dataset complet comporte **50 683 morceaux**, **9 711 301 interactions** et **962 037 utilisateurs**.
        """
    )

    st.subheader("Exemples de clés Redis")
    st.code(
        """track:TRIOREW128F424EAF0:cache       String JSON + TTL
track:TRIOREW128F424EAF0:stats       Hash
user:42:recent_tracks                List
ranking:tracks:global                Sorted Set
recommendations:user:42              String JSON + TTL""",
        language="text",
    )

    st.subheader("Démonstration attendue")
    st.markdown(
        """
        - exécuter le CRUD sur un document Firestore ;
        - comparer une lecture avec cache vide et une lecture depuis Redis ;
        - afficher et laisser expirer un TTL ;
        - simuler des écoutes et observer les compteurs ;
        - générer un classement avec un Sorted Set ;
        - expliquer les index, règles de sécurité, sauvegardes et restaurations.
        """
    )
