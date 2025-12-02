from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from models import db, Favorite, Rating
from tmdb import get_movie_details, get_tmdb_language, get_image_base
from recommender import recommend_for_user

user_bp = Blueprint("user", __name__, url_prefix="/user")


# ────────────────────────────────────────────────
# KEDVENCEK
# ────────────────────────────────────────────────

@user_bp.route("/favorites")
@login_required
def favorites():
    favs = Favorite.query.filter_by(user_id=current_user.id).all()

    movies = []
    for fav in favs:
        movie = get_movie_details(fav.movie_id)
        if movie and "id" in movie:
            movies.append(movie)

    return render_template("favorites.html",
                           movies=movies,
                           image_base=get_image_base())


@user_bp.route("/favorite/add/<int:movie_id>")
@login_required
def add_favorite(movie_id):
    exists = Favorite.query.filter_by(
        user_id=current_user.id,
        movie_id=movie_id
    ).first()

    if not exists:
        db.session.add(Favorite(user_id=current_user.id, movie_id=movie_id))
        db.session.commit()
        flash("Hozzáadva a kedvencekhez!", "success")
    else:
        flash("Ez a film már a kedvencek között van!", "info")

    return redirect(url_for("main.movie_details", movie_id=movie_id))


@user_bp.route("/favorite/remove/<int:movie_id>")
@login_required
def remove_favorite(movie_id):
    fav = Favorite.query.filter_by(
        user_id=current_user.id,
        movie_id=movie_id
    ).first()

    if fav:
        db.session.delete(fav)
        db.session.commit()
        flash("Kedvencekből eltávolítva!", "info")
    else:
        flash("Ez a film nincs a kedvencek között!", "warning")

    return redirect(url_for("user.favorites"))


# ────────────────────────────────────────────────
# ÉRTÉKELÉSEK
# ────────────────────────────────────────────────

@user_bp.route("/ratings")
@login_required
def my_ratings():
    ratings = Rating.query.filter_by(user_id=current_user.id).all()

    movie_data = []
    for r in ratings:
        movie = get_movie_details(r.movie_id)
        if movie:
            movie_data.append({
                "movie": movie,
                "rating": r.rating
            })

    return render_template("my_ratings.html",
                           movie_data=movie_data,
                           image_base=get_image_base())


@user_bp.route("/rating/add/<int:movie_id>", methods=["POST"])
@login_required
def rate_movie(movie_id):
    rating_value = int(request.form.get("rating"))

    rating = Rating.query.filter_by(
        user_id=current_user.id,
        movie_id=movie_id
    ).first()

    if rating:
        rating.rating = rating_value
    else:
        db.session.add(Rating(
            user_id=current_user.id,
            movie_id=movie_id,
            rating=rating_value
        ))

    db.session.commit()
    flash("Értékelés mentve!", "success")
    return redirect(url_for("main.movie_details", movie_id=movie_id))


@user_bp.route("/rating/remove/<int:movie_id>")
@login_required
def remove_rating(movie_id):

    rating = Rating.query.filter_by(
        user_id=current_user.id,
        movie_id=movie_id
    ).first()

    if rating:
        db.session.delete(rating)
        db.session.commit()
        flash("Értékelés eltávolítva!", "success")
    else:
        flash("Nincs ilyen értékelés!", "warning")

    return redirect(url_for("user.my_ratings"))


# ────────────────────────────────────────────────
# AJÁNLÁSOK
# ────────────────────────────────────────────────

@user_bp.route("/recommendations")
@login_required
def recommendations():

    if "recommended_ids" not in session:
        favs = Favorite.query.filter_by(user_id=current_user.id).all()
        favorite_ids = [f.movie_id for f in favs]

        movies = recommend_for_user(favorite_ids)
        session["recommended_ids"] = [m["id"] for m in movies]

    recommended_ids = session["recommended_ids"]

    movies = []
    for mid in recommended_ids:
        movies.append(get_movie_details(mid))

    return render_template(
        "recommendations.html",
        movies=movies,
        image_base=get_image_base()
    )
