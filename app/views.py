"""Seiten des Backoffice. Die Anwendung prüft bewusst keine Geschäftsregeln."""
from secrets import compare_digest
from time import sleep

from flask import Blueprint, abort, current_app, redirect, render_template, request, session, url_for

from . import db

bp = Blueprint("seiten", __name__)
BENUTZER = "sachbearbeiter"
WARTEZEIT_SEKUNDEN = 45
OHNE_ANMELDUNG = ("seiten.login", "seiten.admin_reset", "static")


def _pfad():
    return current_app.config["DB_PATH"]


@bp.before_app_request
def anmeldung_pruefen():
    if request.endpoint not in OHNE_ANMELDUNG and not session.get("benutzer"):
        return redirect(url_for("seiten.login"))


@bp.app_errorhandler(404)
def nicht_gefunden(fehler):
    return render_template("fehler.html", meldung="Seite nicht gefunden"), 404


@bp.route("/")
def start():
    return redirect(url_for("seiten.kundensuche"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    benutzer = request.form.get("benutzer", "")
    passwort = request.form.get("passwort", "")
    passt = compare_digest(benutzer.encode(), BENUTZER.encode()) and compare_digest(
        passwort.encode(), current_app.config["PASSWORT"].encode())
    if not passt:
        return render_template("login.html", meldung="Anmeldung fehlgeschlagen"), 401
    session.clear()
    session["benutzer"] = BENUTZER
    return redirect(url_for("seiten.kundensuche"))


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("seiten.login"))


@bp.route("/kunden")
def kundensuche():
    nr = request.args.get("nr", "").strip()
    return render_template("kunden.html", nr=nr, gesucht="nr" in request.args, kunde=db.kunde(_pfad(), nr))


@bp.route("/kunden/<nr>")
def kundenseite(nr):
    kunde = db.kunde(_pfad(), nr)
    if kunde is None:
        return render_template("fehler.html", meldung="Kunde nicht gefunden"), 404
    return render_template("kunde.html", kunde=kunde, auftraege=db.auftraege(_pfad(), nr))


@bp.route("/kunden/<nr>/freistellung/neu", methods=["GET", "POST"])
def freistellung_neu(nr):
    if request.method == "GET":
        return render_template("freistellung.html", f={"kundennummer": nr, "gueltig_ab": "01.01.2027"})
    daten = {feld: request.form.get(feld, "").strip() for feld in db.FELDER}
    if db.kunde(_pfad(), daten["kundennummer"]) is None:
        return render_template("freistellung.html", f=daten, meldung="Kunde nicht gefunden")
    # Keine weitere Prüfung: das Altsystem nimmt jede Eingabe an.
    bestaetigungsnr = db.speichere_auftrag(_pfad(), daten)
    return redirect(url_for("seiten.bestaetigung", bestaetigungsnr=bestaetigungsnr), code=303)


@bp.route("/bestaetigung/<bestaetigungsnr>")
def bestaetigung(bestaetigungsnr):
    auftrag = db.auftrag(_pfad(), bestaetigungsnr)
    if auftrag is None:
        abort(404)
    if current_app.config["SLOW_CONFIRM"]:
        sleep(WARTEZEIT_SEKUNDEN)  # Störfall: Auftrag ist gespeichert, die Antwort kommt spät
    return render_template("bestaetigung.html", auftrag=auftrag)


@bp.route("/admin/reset", methods=["POST"])
def admin_reset():
    """Setzt die Demo-Daten zurück. Nur vom selben Rechner, ohne Anmeldung."""
    if request.remote_addr != "127.0.0.1":
        abort(403)
    db.reset(_pfad())
    return "Ausgangsdaten wiederhergestellt\n", 200, {"Content-Type": "text/plain; charset=utf-8"}
