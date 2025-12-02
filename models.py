from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ────────────────────────────────────────────────
# USER
# ────────────────────────────────────────────────

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(300), nullable=False)

    # jelszó beállítás
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # jelszó ellenőrzés
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ────────────────────────────────────────────────
# RATING
# ────────────────────────────────────────────────

class Rating(db.Model):
    __tablename__ = "ratings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    movie_id = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=False)

    __table_args__ = (db.UniqueConstraint("user_id", "movie_id"),)


# ────────────────────────────────────────────────
# FAVORITE
# ────────────────────────────────────────────────

class Favorite(db.Model):
    __tablename__ = "favorites"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    movie_id = db.Column(db.Integer, nullable=False)

    __table_args__ = (db.UniqueConstraint("user_id", "movie_id"),)
