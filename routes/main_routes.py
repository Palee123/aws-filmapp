from flask import Blueprint, render_template, request, redirect, url_for, session
from tmdb import (
    get_popular_movies,
    get_movie_details,
    search_movies,
    get_genres,
    get_image_base,
    get_tmdb_language
)
from models import Rating, Favorite
from flask_login import current_user

main_bp = Blueprint("main", __name__)


# ────────────────────────────────────────────────
# Nyelv váltás
# ────────────────────────────────────────────────

@main_bp.route("/set_language/<lang>")
def set_language(lang):
    if lang not in ["hu", "en"]:
        lang = "hu"
    session["lang"] = lang
    return redirect(request.referrer or url_for("main.index"))


# ────────────────────────────────────────────────
# FŐOLDAL
# ────────────────────────────────────────────────

@main_bp.route("/")
def index():
    query = request.args.get("query", "").strip()

    if query:
        # keresési találatok
        movies = search_movies(query)
        return render_template(
            "index.html",
            movies=movies,
            searching=True,
            search_query=query,
            image_base=get_image_base()
        )

    # népszerű filmek
    movies = get_popular_movies()

    return render_template(
        "index.html",
        movies=movies,
        searching=False,
        search_query=None,
        image_base=get_image_base()
    )


# ────────────────────────────────────────────────
# Külön KERESŐ oldal
# ────────────────────────────────────────────────

@main_bp.route("/search")
def search():
    genres = get_genres()
    return render_template("search.html", genres=genres)


# ────────────────────────────────────────────────
# Keresési eredmények
# ────────────────────────────────────────────────

@main_bp.route("/search/results")
def search_results():
    query = request.args.get("query")
    genre_id = request.args.get("genre")

    results = search_movies(query)

    if genre_id and genre_id != "0":
        gid = int(genre_id)
        results = [m for m in results if gid in m.get("genre_ids", [])]

    return render_template(
        "search_results.html",
        results=results,
        image_base=get_image_base()
    )


# ────────────────────────────────────────────────
# Film részletek
# ────────────────────────────────────────────────

@main_bp.route("/movie/<int:movie_id>")
def movie_details(movie_id):
    movie = get_movie_details(movie_id)

    poster = None
    if movie.get("poster_path"):
        poster = get_image_base() + movie["poster_path"]

    # átlag értékelés
    ratings = Rating.query.filter_by(movie_id=movie_id).all()
    avg_rating = (
        sum(r.rating for r in ratings) / len(ratings)
        if ratings else None
    )

    # saját értékelés
    user_rating = None
    if current_user.is_authenticated:
        r = Rating.query.filter_by(
            user_id=current_user.id,
            movie_id=movie_id
        ).first()
        if r:
            user_rating = r.rating

    # kedvenc-e?
    is_favorite = False
    if current_user.is_authenticated:
        fav = Favorite.query.filter_by(
            user_id=current_user.id,
            movie_id=movie_id
        ).first()
        is_favorite = bool(fav)

    return render_template(
        "movie_details.html",
        movie=movie,
        poster=poster,
        avg_rating=avg_rating,
        user_rating=user_rating,
        is_favorite=is_favorite
    )
