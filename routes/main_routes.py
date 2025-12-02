from flask import Blueprint, render_template, request, redirect, url_for, session
from flask_login import login_required, current_user

# TMDb import az új, biztonságos API wrapperből
from tmdb import (
    get_popular_movies,
    get_movie_details,
    get_similar_movies,
    get_genres
)

main_bp = Blueprint("main", __name__)


# -------------------------------------------------------------------
# FŐOLDAL
# -------------------------------------------------------------------
@main_bp.route("/")
def index():
    query = request.args.get("query", "").strip()

    # keresés: egyszerű API megoldás → a popular endpoint helyett keresési URL
    if query:
        from tmdb import safe_tmdb_request, get_tmdb_language

        data = safe_tmdb_request(
            "search/movie",
            params={"query": query, "language": get_tmdb_language()}
        )
        movies = data.get("results", [])

        return render_template(
            "index.html",
            movies=movies,
            searching=True,
            search_query=query
        )

    # nincs keresés → népszerű filmek listája
    movies = get_popular_movies()

    return render_template(
        "index.html",
        movies=movies,
        searching=False,
        search_query=None
    )


# -------------------------------------------------------------------
# NYELVVÁLTÓ
# -------------------------------------------------------------------
@main_bp.route("/set_language/<lang>")
def set_language(lang):
    if lang not in ["hu", "en"]:
        lang = "hu"
    session["lang"] = lang
    return redirect(request.referrer or url_for("main.index"))


# -------------------------------------------------------------------
# KERESŐ OLDAL (űrlap)
# -------------------------------------------------------------------
@main_bp.route("/search")
def search():
    genres = get_genres()
    return render_template("search.html", genres=genres)


# -------------------------------------------------------------------
# KERESÉSI EREDMÉNYEK
# -------------------------------------------------------------------
@main_bp.route("/search/results")
def search_results():
    from tmdb import safe_tmdb_request, get_tmdb_language

    query = request.args.get("query", "")
    genre_id = request.args.get("genre", "0")

    # keresés
    data = safe_tmdb_request(
        "search/movie",
        params={"query": query, "language": get_tmdb_language()}
    )
    results = data.get("results", [])

    # ha van megadott műfaj → szűrés
    if genre_id != "0":
        genre_id = int(genre_id)
        results = [m for m in results if genre_id in m.get("genre_ids", [])]

    return render_template("search_results.html", results=results)


# -------------------------------------------------------------------
# FILM RÉSZLETEK
# -------------------------------------------------------------------
@main_bp.route("/movie/<int:movie_id>")
def movie_details(movie_id):
    from models import Rating, Favorite, db

    movie = get_movie_details(movie_id)

    # kép elérési útvonal
    poster = None
    if movie.get("poster_path"):
        poster = "https://image.tmdb.org/t/p/w500" + movie["poster_path"]

    # átlag értékelés db-ből
    ratings = Rating.query.filter_by(movie_id=movie_id).all()
    avg_rating = (
        sum(r.rating for r in ratings) / len(ratings)
        if ratings else None
    )

    # user saját értékelése
    user_rating = None
    if current_user.is_authenticated:
        r = Rating.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
        if r:
            user_rating = r.rating

    # kedvenc?
    is_favorite = False
    if current_user.is_authenticated:
        fav = Favorite.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
        if fav:
            is_favorite = True

    return render_template(
        "movie_details.html",
        movie=movie,
        poster=poster,
        avg_rating=avg_rating,
        user_rating=user_rating,
        is_favorite=is_favorite
    )
