import re

import pytest

from app import create_app, db

BANNER = "Fiktive Demo-Anwendung, keine echte Bank"
TITEL = "<title>Musterbank Backoffice</title>"
NEU = "/kunden/K10001/freistellung/neu"
AUFTRAG = {"kundennummer": "K10001", "steuer_id": "65183024675", "betrag": "800",
           "gueltig_ab": "01.01.2027", "gemeinsam": "nein", "steuer_id_partner": "",
           "referenz": "FSA-2026-0099"}


@pytest.fixture
def app(tmp_path, monkeypatch):
    for name in ("APP_VERSION", "SLOW_CONFIRM", "MUSTERBANK_PASSWORT", "SECRET_KEY"):
        monkeypatch.delenv(name, raising=False)
    return create_app(tmp_path / "test.db")


@pytest.fixture
def anon(app):
    return app.test_client()


@pytest.fixture
def client(app):
    c = app.test_client()
    r = c.post("/login", data={"benutzer": "sachbearbeiter", "passwort": "demo"})
    assert r.status_code == 302 and r.headers["Location"] == "/kunden"
    return c


def anzahl_auftraege(app, nr="K10001"):
    return len(db.auftraege(app.config["DB_PATH"], nr))


# Anmeldung

@pytest.mark.parametrize("url", ["/", "/kunden", "/kunden?nr=K10001", "/kunden/K10001", NEU,
                                 "/bestaetigung/FS-000117"])
def test_ohne_anmeldung_geht_es_zur_anmeldeseite(anon, url):
    r = anon.get(url)
    assert r.status_code == 302 and r.headers["Location"] == "/login"


def test_auftrag_speichern_ohne_anmeldung_geht_nicht(app, anon):
    r = anon.post(NEU, data=AUFTRAG)
    assert r.status_code == 302 and r.headers["Location"] == "/login"
    assert anzahl_auftraege(app) == 0


def test_anmeldeseite(anon):
    html = anon.get("/login").get_data(as_text=True)
    for element_id in ("benutzer", "passwort", "btn-login"):
        assert f'id="{element_id}"' in html


@pytest.mark.parametrize("benutzer,passwort", [("sachbearbeiter", "falsch"), ("jemand", "demo"), ("", "")])
def test_falsche_anmeldung(anon, benutzer, passwort):
    r = anon.post("/login", data={"benutzer": benutzer, "passwort": passwort})
    assert "Anmeldung fehlgeschlagen" in r.get_data(as_text=True)
    assert anon.get("/kunden").status_code == 302


def test_passwort_aus_umgebungsvariable(tmp_path, monkeypatch):
    monkeypatch.setenv("MUSTERBANK_PASSWORT", "anders")
    c = create_app(tmp_path / "test.db").test_client()
    assert "Anmeldung fehlgeschlagen" in c.post(
        "/login", data={"benutzer": "sachbearbeiter", "passwort": "demo"}).get_data(as_text=True)
    assert c.post("/login", data={"benutzer": "sachbearbeiter", "passwort": "anders"}).status_code == 302


def test_abmelden(client):
    client.get("/logout")
    assert client.get("/kunden").headers["Location"] == "/login"


# Kundensuche und Kundenseite

def test_suchseite(client):
    html = client.get("/kunden").get_data(as_text=True)
    for element_id in ("form-suche", "suche-kundennummer", "btn-suchen", "suchergebnis"):
        assert f'id="{element_id}"' in html
    assert 'name="nr"' in html


def test_suche_findet_k10001(client):
    html = client.get("/kunden?nr=K10001").get_data(as_text=True)
    ergebnis = re.search(r'<p id="suchergebnis">(.*?)</p>', html, re.S).group(1)
    assert re.sub(r"<[^>]+>", "", ergebnis).strip() == "Kunde gefunden: Erika Beispiel"
    assert 'href="/kunden/K10001"' in ergebnis


@pytest.mark.parametrize("nr", ["K99999", "x"])
def test_suche_unbekannt(client, nr):
    html = client.get(f"/kunden?nr={nr}").get_data(as_text=True)
    assert re.search(r'<p id="suchergebnis">\s*Kunde nicht gefunden\s*</p>', html)


def test_kundenseite_zeigt_bestand(client):
    html = client.get("/kunden/K10009").get_data(as_text=True)
    assert '<table id="auftraege">' in html
    for spalte in ("Bestätigungsnr.", "Referenz", "Betrag", "Gemeinsam", "Gültig ab"):
        assert f"<th>{spalte}</th>" in html
    for wert in ("FS-000117", "FSA-2025-0940", "600", "01.01.2026"):
        assert f"<td>{wert}</td>" in html
    assert 'href="/kunden/K10009/freistellung/neu"' in html


def test_kundenseite_unbekannt(client):
    r = client.get("/kunden/K99999")
    assert r.status_code == 404
    assert "Kunde nicht gefunden" in r.get_data(as_text=True)


# Neuer Auftrag

def test_formular_hat_alle_elemente(client):
    html = client.get(NEU).get_data(as_text=True)
    assert '<form id="form-freistellung" method="post">' in html
    for feld in ("kundennummer", "steuer_id", "betrag", "gueltig_ab", "gemeinsam",
                 "steuer_id_partner", "referenz"):
        assert f'id="{feld}" name="{feld}"' in html
    assert '<input id="kundennummer" name="kundennummer" value="K10001">' in html
    assert '<button id="btn-abbrechen" type="button"' in html
    assert '<button id="btn-speichern" type="submit">Speichern</button>' in html
    assert "btn-uebernehmen" not in html
    assert html.count('type="submit"') == 1


def test_auftrag_speichern_liefert_bestaetigungsnummer(client):
    r = client.post(NEU, data=AUFTRAG)
    assert r.status_code == 303 and r.headers["Location"] == "/bestaetigung/FS-000123"
    html = client.get("/bestaetigung/FS-000123").get_data(as_text=True)
    assert '<b id="bestaetigungsnr">FS-000123</b>' in html

    html = client.get("/kunden/K10001").get_data(as_text=True)
    zeile = re.search(r"<tr>\s*<td>FS-000123</td>.*?</tr>", html, re.S).group(0)
    assert re.findall(r"<td>(.*?)</td>", zeile) == ["FS-000123", "FSA-2026-0099", "800", "nein", "01.01.2027"]

    r = client.post(NEU, data={**AUFTRAG, "referenz": "FSA-2026-0100"})
    assert r.headers["Location"] == "/bestaetigung/FS-000124"


def test_kundennummer_aus_dem_formular_zaehlt(app, client):
    client.post(NEU, data={**AUFTRAG, "kundennummer": " K10002 "})
    assert anzahl_auftraege(app, "K10001") == 0
    assert anzahl_auftraege(app, "K10002") == 1


def test_unbekannter_kunde_wird_nicht_gespeichert(app, client):
    r = client.post(NEU, data={**AUFTRAG, "kundennummer": "K99999"})
    html = r.get_data(as_text=True)
    assert r.status_code == 200
    assert "Kunde nicht gefunden" in html
    assert 'value="K99999"' in html and 'value="FSA-2026-0099"' in html
    assert db.auftraege(app.config["DB_PATH"], "K99999") == []
    assert client.get("/bestaetigung/FS-000123").status_code == 404


def test_keine_fachliche_pruefung(app, client):
    """Die Anwendung nimmt alles an. Die Regeln muss prüfen, wer erfasst."""
    unsinn = {**AUFTRAG, "steuer_id": "abc", "betrag": "-5000,50", "gemeinsam": "ja",
              "steuer_id_partner": "", "gueltig_ab": "irgendwann", "referenz": ""}
    for _ in range(2):
        assert client.post(NEU, data=unsinn).status_code == 303
    assert anzahl_auftraege(app) == 2
    assert "<td>-5000,50</td>" in client.get("/kunden/K10001").get_data(as_text=True)


def test_eingaben_werden_maskiert(client):
    client.post(NEU, data={**AUFTRAG, "referenz": "<script>alert(1)</script>"})
    assert "<script>" not in client.get("/kunden/K10001").get_data(as_text=True)


def test_bestaetigung_unbekannt(client):
    assert client.get("/bestaetigung/FS-999999").status_code == 404


# Schalter für Störfälle

def test_version_2_benennt_den_knopf_um(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_VERSION", "2")
    c = create_app(tmp_path / "test.db").test_client()
    c.post("/login", data={"benutzer": "sachbearbeiter", "passwort": "demo"})
    html = c.get(NEU).get_data(as_text=True)
    assert '<button id="btn-uebernehmen" type="submit">Übernehmen</button>' in html
    assert "btn-speichern" not in html and "Speichern" not in html


def test_langsame_bestaetigung_speichert_vor_der_wartezeit(tmp_path, monkeypatch):
    monkeypatch.setenv("SLOW_CONFIRM", "1")
    app = create_app(tmp_path / "test.db")
    c = app.test_client()
    c.post("/login", data={"benutzer": "sachbearbeiter", "passwort": "demo"})
    wartezeiten = []

    def sleep(sekunden):
        wartezeiten.append((sekunden, anzahl_auftraege(app)))

    monkeypatch.setattr("app.views.sleep", sleep)
    r = c.post(NEU, data=AUFTRAG, follow_redirects=True)
    assert '<b id="bestaetigungsnr">FS-000123</b>' in r.get_data(as_text=True)
    assert wartezeiten == [(45, 1)]


def test_ohne_schalter_keine_wartezeit(client, monkeypatch):
    monkeypatch.setattr("app.views.sleep", lambda s: pytest.fail("darf nicht warten"))
    assert client.post(NEU, data=AUFTRAG, follow_redirects=True).status_code == 200


# Zurücksetzen

def test_reset_stellt_die_ausgangsdaten_wieder_her(app, anon, client):
    client.post(NEU, data=AUFTRAG)
    assert anzahl_auftraege(app) == 1
    r = anon.post("/admin/reset")   # ohne Anmeldung, damit ein Skript es aufrufen kann
    assert r.status_code == 200
    assert anzahl_auftraege(app) == 0
    assert anzahl_auftraege(app, "K10009") == 1
    assert client.post(NEU, data=AUFTRAG).headers["Location"] == "/bestaetigung/FS-000123"


def test_reset_nur_lokal_und_nur_per_post(app, client):
    client.post(NEU, data=AUFTRAG)
    assert client.post("/admin/reset", environ_base={"REMOTE_ADDR": "192.168.0.7"}).status_code == 403
    assert client.get("/admin/reset").status_code == 405
    assert anzahl_auftraege(app) == 1


def test_datenbank_bleibt_beim_neustart_erhalten(tmp_path):
    pfad = tmp_path / "test.db"
    c = create_app(pfad).test_client()
    c.post("/login", data={"benutzer": "sachbearbeiter", "passwort": "demo"})
    c.post(NEU, data=AUFTRAG)
    assert anzahl_auftraege(create_app(pfad)) == 1


# Jede Seite

@pytest.mark.parametrize("url", ["/kunden", "/kunden?nr=K10001", "/kunden/K10009", NEU,
                                 "/bestaetigung/FS-000117", "/kunden/K99999", "/gibt-es-nicht"])
def test_jede_seite_hat_titel_und_hinweis(client, url):
    html = client.get(url).get_data(as_text=True)
    assert TITEL in html and BANNER in html


def test_anmeldeseite_hat_titel_und_hinweis(anon):
    for r in (anon.get("/login"), anon.post("/login", data={})):
        html = r.get_data(as_text=True)
        assert TITEL in html and BANNER in html
