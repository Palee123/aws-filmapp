import os

def load_config(app):
    """Betölti a konfigurációkat az app számára."""

    # Secret key betöltése
    secret_path = os.path.join(app.root_path, "secret_key.txt")
    with open(secret_path, "r") as f:
        app.config["SECRET_KEY"] = f.read().strip()

    # TMDb API kulcs betöltése
    tmdb_path = os.path.join(app.root_path, "tmdb_key.txt")
    with open(tmdb_path, "r") as f:
        app.config["TMDB_API_KEY"] = f.read().strip()

    # Jelenleg SQLite — később könnyen átírható RDS-re
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
