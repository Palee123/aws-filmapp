from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_required, current_user
from models import db, Rating, Favorite
from tmdb import (
    get_movie_details,
    get_similar_movies,
    get_tmdb_language,
    safe_tmdb_request
)

user_bp = Blueprint("user", __name__)


# -------------------------------------------------------------------
# KEDVENCEK LISTÁJA
# -------------------------------------------------------------------
@user_bp.route("/favorites")
@login_required
def favorites():
    favs = Favorite.query.filter_by(user_id=current_user.id).all()

    movies = []
    lang_code = get_tmdb_language()

    for fav in favs:
        movie = safe_tmdb_request(
            f"movie/{fav.movie_id}",
            params={"language": lang_code},
            fallback={}
        )
        if movie and "id" in movie:
            movies.append(movie)

    return render_template("favorites.html", movies=movies)


# -------------------------------------------------------------------
# KEDVENC HOZZÁADÁSA
# -------------------------------------------------------------------
@user_bp.route("/favorite/<int:movie_id>")
@login_required
def add_favorite(movie_id):
    existing = Favorite.query.filter_by(
        user_id=current_user.id,
        movie_id=movie_id
    ).first()

    if existing:
        flash("Ez a film már a kedvencek között van!", "info")
    else:
        fav = Favorite(user_id=current_user.id, movie_id=movie_id)
        db.session.add(fav)
        db.session.commit()
        flash("Hozzáadva a kedvencekhez!", "success")

    return redirect(url_for("main.movie_details", movie_id=movie_id))


# -------------------------------------------------------------------
# KEDVENC TÖRLÉSE
# -------------------------------------------------------------------
@user_bp.route("/remove_favorite/<int:movie_id>")
@login_required
def remove_favorite(movie_id):
    fav = Favorite.query.filter_by(
        user_id=current_user.id,
        movie_id=movie_id
    ).first()

    if fav:
        db.session.delete(fav)
        db.session.commit()
        flash("Eltávolítva a kedvencekből!", "info")
    else:
        flash("Ez a film nincs a kedvenceid között!", "warning")

    return redirect(url_for("user.favorites"))


# -------------------------------------------------------------------
# SAJÁT ÉRTÉKELÉSEK
# -------------------------------------------------------------------
@user_bp.route("/my_ratings")
@login_required
def my_ratings():
    ratings = Rating.query.filter_by(user_id=current_user.id).all()

    movie_data = []
    lang_code = get_tmdb_language()

    for r in ratings:
        movie = safe_tmdb_request(
            f"movie/{r.movie_id}",
            params={"language": lang_code},
            fallback={}
        )
        if movie and "id" in movie:
            movie_data.append({"movie": movie, "rating": r.rating})

    return render_template("my_ratings.html", movie_data=movie_data)


# -------------------------------------------------------------------
# ÉRTÉKELÉS MENTÉSE / FRISSÍTÉSE
# -------------------------------------------------------------------
@user_bp.route("/rate/<int:movie_id>", methods=["POST"])
@login_required
def rate_movie(movie_id):
    value = int(request.form.get("rating"))

    existing = Rating.query.filter_by(
        user_id=current_user.id,
        movie_id=movie_id
    ).first()

    if existing:
        existing.rating = value
    else:
        new_rating = Rating(
            user_id=current_user.id,
            movie_id=movie_id,
            rating=value
        )
        db.session.add(new_rating)

    db.session.commit()

    flash("Értékelés mentve!", "success")
    return redirect(url_for("main.movie_details", movie_id=movie_id))


# -------------------------------------------------------------------
# ÉRTÉKELÉS TÖRLÉSE
# -------------------------------------------------------------------
@user_bp.route("/remove_rating/<int:movie_id>")
@login_required
def remove_rating(movie_id):
    r = Rating.query.filter_by(
        user_id=current_user.id,
        movie_id=movie_id
    ).first()

    if r:
        db.session.delete(r)
        db.session.commit()
        flash("Értékelés eltávolítva!", "success")
    else:
        flash("Nem található értékelés.", "warning")

    return redirect(url_for("user.my_ratings"))


# -------------------------------------------------------------------
# AJÁNLÓRENDSZER
# -------------------------------------------------------------------
@user_bp.route("/recommendations")
@login_required
def recommendations():
    favs = Favorite.query.filter_by(user_id=current_user.id).all()
    favorite_ids = [f.movie_id for f in favs]

    if not favorite_ids:
        return render_template("recommendations.html", movies=[])

    # ajánlás az első kedvenc alapján
    rec = get_similar_movies(favorite_ids[0], limit=10)

    # session cache (opcionális)
    session["recommended_ids"] = [m["id"] for m in rec]

    # filmadatok letöltése
    movies = []
    for mid in session["recommended_ids"]:
        movie = safe_tmdb_request(
            f"movie/{mid}",
            params={"language": get_tmdb_language()},
            fallback={}
        )
        movies.append(movie)

    return render_template("recommendations.html", movies=movies)
