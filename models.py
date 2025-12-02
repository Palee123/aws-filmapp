from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ---------------------------------------------------------
# USER MODEL
# ---------------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(300), nullable=False)

    # Kapcsolatok 
    ratings = db.relationship("Rating", backref="user", lazy="dynamic", cascade="all, delete")
    favorites = db.relationship("Favorite", backref="user", lazy="dynamic", cascade="all, delete")

    # Jelszó hash-elés
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Jelszó ellenőrzés
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ---------------------------------------------------------
# RATING MODEL
# ---------------------------------------------------------
class Rating(db.Model):
    __tablename__ = "ratings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    movie_id = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=False)

    # User + Movie egyedi (nem lehet kétszer értékelni ugyanazt a filmet)
    __table_args__ = (
        db.UniqueConstraint("user_id", "movie_id", name="unique_user_movie_rating"),
    )


# ---------------------------------------------------------
# FAVORITE MODEL
# ---------------------------------------------------------
class Favorite(db.Model):
    __tablename__ = "favorites"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    movie_id = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("user_id", "movie_id", name="unique_user_favorite"),
    )
