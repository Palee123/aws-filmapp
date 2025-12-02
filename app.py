from flask import Flask
from config import load_config

# modellek + db import
from models import db, User, Rating, Favorite

# blueprint importok
from routes.main_routes import main_bp
from routes.auth_routes import auth_bp
from routes.user_routes import user_bp

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    # konfigurációk betöltése (secret_key, tmdb key, adatbázis stb.)
    load_config(app)

    # db inicializálása
    db.init_app(app)

    # blueprint-ek regisztrálása
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)

    # adatbázis létrehozása
    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
