import os
import requests
from flask import session

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
tmdb_key_path = os.path.join(BASE_DIR, "tmdb_key.txt")

with open(tmdb_key_path, "r", encoding="utf-8") as f:
    TMDB_API_KEY = f.read().strip()

TMDB_BASE_URL = "https://api.themoviedb.org/3"


def get_tmdb_language():
    #Nyelvkód a session alapján.
    return "hu-HU" if session.get("lang", "hu") == "hu" else "en-US"


def safe_tmdb_request(endpoint, params=None, fallback=None):
    #Biztonságos API wrapper nem dob hibát
    if params is None:
        params = {}

    url = f"{TMDB_BASE_URL}/{endpoint}"
    params.update({"api_key": TMDB_API_KEY})

    try:
        response = requests.get(url, params=params, timeout=5)
        return response.json()
    except Exception:
        return fallback or {}


# ---------------------------------------------------------
# POPULAR MOVIES
# ---------------------------------------------------------
def get_popular_movies():
    data = safe_tmdb_request(
        "movie/popular",
        params={"language": get_tmdb_language()},
        fallback={"results": []}
    )
    return data.get("results", [])


# ---------------------------------------------------------
# MOVIE DETAILS
# ---------------------------------------------------------
def get_movie_details(movie_id):
    data = safe_tmdb_request(
        f"movie/{movie_id}",
        params={"language": get_tmdb_language()},
        fallback={}
    )
    return data


# ---------------------------------------------------------
# SIMILAR MOVIES  ← EZ KELL NEKED
# ---------------------------------------------------------
def get_similar_movies(movie_id, limit=10):
    data = safe_tmdb_request(
        f"movie/{movie_id}/similar",
        params={"language": get_tmdb_language()},
        fallback={"results": []}
    )
    return data.get("results", [])[:limit]


# ---------------------------------------------------------
# GENRE LIST
# ---------------------------------------------------------
def get_genres():
    data = safe_tmdb_request(
        "genre/movie/list",
        params={"language": get_tmdb_language()},
        fallback={"genres": []}
    )
    return data.get("genres", [])
