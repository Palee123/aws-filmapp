from flask import Flask, session
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

from config import load_config
from models import db, User
from routes.main_routes import main_bp
from routes.auth_routes import auth_bp
from routes.user_routes import user_bp


# ────────────────────────────────────────────────
# APP inicializálás
# ────────────────────────────────────────────────
def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # konfiguráció betöltése (secret key, TMDB key, DB URI)
    load_config(app)

    # SQLAlchemy inicializálása
    db.init_app(app)

    # Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    from models import User  # importálni kell, hogy user_loader működjön

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Nyelv beszúrása a template-ekbe
    @app.context_processor
    def inject_lang():
        return {"lang": session.get("lang", "hu")}

    # Blueprint-ek regisztrálása
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)

    # DB táblák létrehozása első indításkor
    with app.app_context():
        db.create_all()

    return app


# ────────────────────────────────────────────────
# Futás
# ────────────────────────────────────────────────
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
