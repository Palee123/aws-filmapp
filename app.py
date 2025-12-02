from flask import Flask
from config import load_config
from models import db, User, Rating, Favorite
from routes.main_routes import main_bp
from routes.auth_routes import auth_bp
from routes.user_routes import user_bp

from flask_login import LoginManager, current_user

login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    """Flask-Login user betöltése."""
    return User.query.get(int(user_id))


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # config betöltése (keys, DB stb.)
    load_config(app)

    # adatbázis inicializálása
    db.init_app(app)

    # login manager
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # current_user sablonokhoz
    @app.context_processor
    def inject_user():
        return dict(current_user=current_user)

    # route blueprintek
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)

    # DB táblák létrehozása
    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
