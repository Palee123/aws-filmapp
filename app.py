from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
import os
import requests

# Ez a fájl tartalmazza az alkalmazás teljes backend logikáját:
#  - Flask alapbeállítások
#  - Secret key és TMDb API kulcs betöltése
#  - SQLite adatbázis konfiguráció + SQLAlchemy modellek:
#         * User (regisztráció, belépés)
#         * Rating (felhasználói értékelések)
#         * Favorite (kedvencek listája)
#  - Flask-Login alapú hitelesítés:
#         * login, logout
#         * user_loader
#  - TMDb API kommunikáció:
#         * népszerű filmek lekérése
#         * film részletek lekérése
#         * műfajok lekérése
#         * keresés kezelése
#  - Route-ok:
#         * /                  → főoldal (populáris filmek)
#         * /register          → regisztráció
#         * /login             → bejelentkezés
#         * /logout            → kijelentkezés
#         * /search            → kereső oldal
#         * /search/results    → keresési eredmények
#         * /movie/<id>        → film részletei és értékelés
#         * /favorite/<id>     → kedvencekhez adás
#         * /favorites         → saját kedvencek listája
#         * /rate/<id>         → film értékelése
#         * /my_ratings        → saját értékelések listája
#         * /set_language/<lang> → nyelvváltás HU/EN
#  - Template-ek számára biztosított globális változók (lang)
#  - Alkalmazás indítása (debug módban)

# ────────────────────────────────────────────────
# APP ALAP BEÁLLÍTÁS
# ────────────────────────────────────────────────

# instance_relative_config=True → az instance mappából tudsz olvasni titkos fájlokat
app = Flask(app_name := __name__, instance_relative_config=True)

# Secret key betöltése egy külön fájlból (biztonságosabb, mintha kódban lenne)
secret_path = os.path.join(app.root_path, "secret_key.txt")
with open(secret_path, "r") as f:
    app.config["SECRET_KEY"] = f.read().strip()

# TMDb API kulcs betöltése
tmdb_key_path = os.path.join(app.root_path, "tmdb_key.txt")
with open(tmdb_key_path, "r") as f:
    TMDB_API_KEY = f.read().strip()


# ────────────────────────────────────────────────
# GLOBÁLIS NYELV KEZELÉS A TEMPLATE-EKBEN
# ────────────────────────────────────────────────

@app.context_processor
def inject_lang():
    """A template-ekben automatikusan elérhető lesz a session-ben tárolt nyelv."""
    return {"lang": session.get("lang", "hu")}

def get_tmdb_language():
    """Visszaadja a TMDb API által elvárt nyelvi kódot."""
    lang = session.get("lang", "hu")
    return "en-US" if lang == "en" else "hu-HU"


# TMDb API alap URL-ek
TMDB_BASE_URL = "https://api.themoviedb.org/3"
IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"


# ────────────────────────────────────────────────
# ADATBÁZIS beállítások (SQLite)
# ────────────────────────────────────────────────

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# ────────────────────────────────────────────────
# LOGIN KEZELŐ
# ────────────────────────────────────────────────

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # erre az oldalra dob át, ha védezett route-ot nyitsz meg


# ────────────────────────────────────────────────
# USER MODELL (tábla)
# ────────────────────────────────────────────────

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(300), nullable=False)

    # Jelszó hash-elése
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Jelszó ellenőrzése
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ────────────────────────────────────────────────
# RATING TÁBLA (egy user 1 filmet csak 1x értékelhet)
# ────────────────────────────────────────────────

class Rating(db.Model):
    __tablename__ = "ratings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    movie_id = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=False)

    # Egyszer egy user csak egyszer értékelhet egy filmet
    __table_args__ = (db.UniqueConstraint("user_id", "movie_id"),)


# ────────────────────────────────────────────────
# FAVORITES TÁBLA
# ────────────────────────────────────────────────

class Favorite(db.Model):
    __tablename__ = "favorites"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    movie_id = db.Column(db.Integer, nullable=False)

    __table_args__ = (db.UniqueConstraint("user_id", "movie_id"),)


# Flask-Login user loader: visszaadja a user objektumot ID alapján
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ────────────────────────────────────────────────
# TMDB API – népszerű filmek lekérése
# ────────────────────────────────────────────────

def get_popular_movies():
    url = f"{TMDB_BASE_URL}/movie/popular"
    params = {
        "api_key": TMDB_API_KEY,
        "language": get_tmdb_language(),
        "page": 1
    }
    response = requests.get(url, params=params).json()
    return response.get("results", [])


# ────────────────────────────────────────────────
# FŐOLDAL
# ────────────────────────────────────────────────

@app.route("/")
def index():
    movies = get_popular_movies()
    return render_template("index.html", movies=movies, image_base=IMAGE_BASE_URL)


# ────────────────────────────────────────────────
# NYELVVÁLTÁS
# ────────────────────────────────────────────────

@app.route("/set_language/<lang>")
def set_language(lang):
    if lang not in ["hu", "en"]:
        lang = "hu"
    session["lang"] = lang
    return redirect(request.referrer or url_for("index"))


# ────────────────────────────────────────────────
# REGISZTRÁCIÓ
# ────────────────────────────────────────────────

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # Form adatok
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # Ellenőrzés, hogy létezik-e ilyen user
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            flash("Ez a felhasználónév vagy email már létezik!", "danger")
            return redirect(url_for("register"))

        # Új user létrehozása
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("Sikeres regisztráció! Jelentkezz be!", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# ────────────────────────────────────────────────
# BEJELENTKEZÉS
# ────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username_or_email = request.form.get("username")
        password = request.form.get("password")

        # Felhasználó keresése username vagy email alapján
        user = User.query.filter(
            (User.username == username_or_email) |
            (User.email == username_or_email)
        ).first()

        # Jelszó ellenőrzés
        if user and user.check_password(password):
            login_user(user)
            flash("Sikeres bejelentkezés!", "success")
            return redirect(url_for("index"))

        flash("Hibás adatok!", "danger")

    return render_template("login.html")


# ────────────────────────────────────────────────
# KIJELENTKEZÉS
# ────────────────────────────────────────────────

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sikeresen kijelentkeztél!", "info")
    return redirect(url_for("login"))


# ────────────────────────────────────────────────
# KERESŐ FELÜLET
# ────────────────────────────────────────────────

@app.route("/search")
def search():
    genres = get_genres()
    return render_template("search.html", genres=genres)


@app.route("/search/results")
def search_results():
    query = request.args.get("query")
    genre_id = request.args.get("genre")

    # TMDb keresési lekérdezés
    params = {
        "api_key": TMDB_API_KEY,
        "language": get_tmdb_language(),
        "query": query,
    }
    url = f"{TMDB_BASE_URL}/search/movie"
    response = requests.get(url, params=params).json()

    results = response.get("results", [])

    # Műfaj szerinti szűrés
    if genre_id and genre_id != "0":
        genre_id = int(genre_id)
        results = [m for m in results if genre_id in m.get("genre_ids", [])]

    return render_template("search_results.html",
                           results=results,
                           image_base=IMAGE_BASE_URL)


# ────────────────────────────────────────────────
# FILM RÉSZLETEK OLDAL
# ────────────────────────────────────────────────

@app.route("/movie/<int:movie_id>")
def movie_details(movie_id):
    # Film adatok lekérése
    url = f"{TMDB_BASE_URL}/movie/{movie_id}"
    params = {"api_key": TMDB_API_KEY, "language": get_tmdb_language()}
    movie = requests.get(url, params=params).json()

    # Poster kép URL
    poster = IMAGE_BASE_URL + movie["poster_path"] if movie.get("poster_path") else None

    # Átlag értékelés adatbázisból
    ratings = Rating.query.filter_by(movie_id=movie_id).all()
    avg_rating = sum(r.rating for r in ratings) / len(ratings) if ratings else None

    # Felhasználó saját értékelése
    user_rating = None
    if current_user.is_authenticated:
        r = Rating.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
        if r:
            user_rating = r.rating

    # Kedvenc-e?
    is_favorite = False
    if current_user.is_authenticated:
        fav = Favorite.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()
        is_favorite = bool(fav)

    return render_template("movie_details.html",
                           movie=movie,
                           poster=poster,
                           avg_rating=avg_rating,
                           user_rating=user_rating,
                           is_favorite=is_favorite)


# ────────────────────────────────────────────────
# SAJÁT KEDVENCEK
# ────────────────────────────────────────────────

@app.route("/favorites")
@login_required
def favorites():
    favorites = Favorite.query.filter_by(user_id=current_user.id).all()

    movies = []
    lang_code = get_tmdb_language()

    # Minden kedvenc filmhez lekérjük a részleteket TMDb-ből
    for fav in favorites:
        url = f"{TMDB_BASE_URL}/movie/{fav.movie_id}"
        params = {"api_key": TMDB_API_KEY, "language": lang_code}
        movie = requests.get(url, params=params).json()
        if movie and "id" in movie:
            movies.append(movie)

    return render_template("favorites.html",
                           movies=movies,
                           image_base=IMAGE_BASE_URL)


@app.route("/remove_favorite/<int:movie_id>")
@login_required
def remove_favorite(movie_id):
    """Kedvenc törlése."""
    fav = Favorite.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()

    if fav:
        db.session.delete(fav)
        db.session.commit()
        flash("Kedvencekből eltávolítva!", "info")
    else:
        flash("Ez a film nincs a kedvencek között!", "warning")

    return redirect(request.referrer or url_for("favorites"))


# ────────────────────────────────────────────────
# SAJÁT ÉRTÉKELÉSEK LISTÁJA
# ────────────────────────────────────────────────

@app.route("/my_ratings")
@login_required
def my_ratings():
    ratings = Rating.query.filter_by(user_id=current_user.id).all()

    movie_data = []
    lang_code = get_tmdb_language()

    # Minden értékeléshez lekérjük a film adatait
    for r in ratings:
        url = f"{TMDB_BASE_URL}/movie/{r.movie_id}"
        params = {"api_key": TMDB_API_KEY, "language": lang_code}
        movie = requests.get(url, params=params).json()

        if movie and "id" in movie:
            movie_data.append({
                "movie": movie,
                "rating": r.rating
            })

    return render_template("my_ratings.html",
                           movie_data=movie_data,
                           image_base=IMAGE_BASE_URL)


# ────────────────────────────────────────────────
# ÉRTÉKELÉS MENTÉSE
# ────────────────────────────────────────────────

@app.route("/rate/<int:movie_id>", methods=["POST"])
@login_required
def rate_movie(movie_id):
    rating_value = int(request.form.get("rating"))

    # Megnézzük, hogy a user már értékelte-e
    existing = Rating.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()

    if existing:
        existing.rating = rating_value
    else:
        new_rating = Rating(user_id=current_user.id, movie_id=movie_id, rating=rating_value)
        db.session.add(new_rating)

    db.session.commit()
    flash("Sikeresen értékelted a filmet!", "success")
    return redirect(url_for("movie_details", movie_id=movie_id))


# ────────────────────────────────────────────────
# KEDVENC HOZZÁADÁSA
# ────────────────────────────────────────────────

@app.route("/favorite/<int:movie_id>")
@login_required
def add_favorite(movie_id):
    fav = Favorite.query.filter_by(user_id=current_user.id, movie_id=movie_id).first()

    if not fav:
        new_fav = Favorite(user_id=current_user.id, movie_id=movie_id)
        db.session.add(new_fav)
        db.session.commit()
        flash("Hozzáadva a kedvencekhez!", "success")
    else:
        flash("Ez a film már a kedvencek között van!", "info")

    return redirect(url_for("movie_details", movie_id=movie_id))


# ────────────────────────────────────────────────
# TMDb MŰFAJOK LEKÉRÉSE
# ────────────────────────────────────────────────

def get_genres():
    url = f"{TMDB_BASE_URL}/genre/movie/list?api_key={TMDB_API_KEY}&language={get_tmdb_language()}"
    response = requests.get(url).json()
    return response.get("genres", [])


# ────────────────────────────────────────────────
# ADATBÁZIS LÉTREHOZÁSA INDULÁSKOR
# ────────────────────────────────────────────────

with app.app_context():
    db.create_all()


# ────────────────────────────────────────────────
# APP FUTTATÁSA
# ────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)
