from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required
from models import db, User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# ────────────────────────────────────────────────
# REGISZTRÁCIÓ
# ────────────────────────────────────────────────

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        # Ellenőrzés, hogy létezik-e
        existing = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing:
            flash("Ez a felhasználónév vagy email már létezik!", "danger")
            return redirect(url_for("auth.register"))

        # Új user létrehozása
        new_user = User(username=username, email=email)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash("Sikeres regisztráció! Jelentkezz be!", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


# ────────────────────────────────────────────────
# BEJELENTKEZÉS
# ────────────────────────────────────────────────

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username_or_email = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter(
            (User.username == username_or_email) |
            (User.email == username_or_email)
        ).first()

        if user and user.check_password(password):
            login_user(user)
            flash("Sikeres bejelentkezés!", "success")
            return redirect(url_for("main.index"))
        else:
            flash("Hibás adatok!", "danger")

    return render_template("login.html")


# ────────────────────────────────────────────────
# KIJELENTKEZÉS
# ────────────────────────────────────────────────

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sikeresen kijelentkeztél!", "info")
    return redirect(url_for("auth.login"))
