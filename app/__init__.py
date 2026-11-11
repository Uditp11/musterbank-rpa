"""Musterbank Backoffice: fiktive Demo-Anwendung, keine echte Bank."""
import os
from pathlib import Path

from flask import Flask

from . import db, views


def create_app(db_path=None):
    """Erzeugt die Anwendung. Ohne db_path liegt die Datenbank neben dem Code."""
    app = Flask(__name__)
    # Fester Standardwert reicht für die lokale Demo, sonst SECRET_KEY setzen.
    app.secret_key = os.environ.get("SECRET_KEY", "musterbank-demo")
    app.config.update(
        DB_PATH=str(db_path or Path(__file__).with_name("musterbank.db")),
        PASSWORT=os.environ.get("MUSTERBANK_PASSWORT", "demo"),
        # Schalter für Störfälle, werden beim Start gelesen
        VERSION_2=os.environ.get("APP_VERSION") == "2",
        SLOW_CONFIRM=os.environ.get("SLOW_CONFIRM") == "1",
        SESSION_COOKIE_SAMESITE="Lax",
    )
    db.init(app.config["DB_PATH"])
    app.register_blueprint(views.bp)
    return app
