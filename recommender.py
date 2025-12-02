import os
import requests
from flask import session

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
tmdb_key_path = os.path.join(BASE_DIR, "tmdb_key.txt")

with open(tmdb_key_path, "r", encoding="utf-8") as f:
    TMDB_API_KEY = f.read().strip()

TMDB_BASE_URL = "https://api.themoviedb.org/3"


def get_tmdb_language():
    """Nyelvkód a session alapján."""
    return "hu-HU" if session.get("lang", "hu") == "hu" else "en-US"


def get_similar_movies(movie_id, limit=10):
    """TMDb 'similar movies' – gyors, egyszerű ajánló alap."""
    url = f"{TMDB_BASE_URL}/movie/{movie_id}/similar"
    params = {
        "api_key": TMDB_API_KEY,
        "language": get_tmdb_language()
    }
    r = requests.get(url, params=params).json()
    return r.get("results", [])[:limit]


def recommend_for_user(favorite_movie_ids):
    """
    Nagyon egyszerű ajánló:
      - ha van legalább 1 kedvenc → az első kedvenc filmhez kérünk hasonló filmeket.
      - ha nincs kedvenc → nincs ajánlás.
    """
    if not favorite_movie_ids:
        return []

    ref_id = favorite_movie_ids[0]   # első kedvenc
    similar = get_similar_movies(ref_id, limit=10)

    # ne ajánlja vissza ugyanazt a filmet
    result = [m for m in similar if m.get("id") != ref_id]

    return result
