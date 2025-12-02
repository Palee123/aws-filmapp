import requests
from flask import current_app, session

TMDB_BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


# ────────────────────────────────────────────────
# Nyelv lekérése
# ────────────────────────────────────────────────

def get_tmdb_language():
    lang = session.get("lang", "hu")
    return "en-US" if lang == "en" else "hu-HU"


# ────────────────────────────────────────────────
# Népszerű filmek
# ────────────────────────────────────────────────

def get_popular_movies():
    url = f"{TMDB_BASE_URL}/movie/popular"
    params = {
        "api_key": current_app.config["TMDB_API_KEY"],
        "language": get_tmdb_language(),
        "page": 1
    }
    response = requests.get(url, params=params).json()
    print("POPULAR RAW RESPONSE:", response)  # <---- EZT TEDD BE
    return response.get("results", [])



# ────────────────────────────────────────────────
# Film részletei
# ────────────────────────────────────────────────

def get_movie_details(movie_id):
    url = f"{TMDB_BASE_URL}/movie/{movie_id}"
    params = {
        "api_key": current_app.config["TMDB_API_KEY"],
        "language": get_tmdb_language()
    }
    return requests.get(url, params=params).json()


# ────────────────────────────────────────────────
# Keresés
# ────────────────────────────────────────────────

def search_movies(query):
    url = f"{TMDB_BASE_URL}/search/movie"
    params = {
        "api_key": current_app.config["TMDB_API_KEY"],
        "language": get_tmdb_language(),
        "query": query
    }
    response = requests.get(url, params=params).json()
    return response.get("results", [])


# ────────────────────────────────────────────────
# Műfajok lekérése
# ────────────────────────────────────────────────

def get_genres():
    url = f"{TMDB_BASE_URL}/genre/movie/list"
    params = {
        "api_key": current_app.config["TMDB_API_KEY"],
        "language": get_tmdb_language(),
    }
    response = requests.get(url, params=params).json()
    return response.get("genres", [])


# Külső modulok számára is exportáljuk az IMAGE_BASE_URL-t
def get_image_base():
    return IMAGE_BASE_URL
