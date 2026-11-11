"""Datenhaltung in SQLite. Die Ausgangsdaten kommen aus data/seed_kunden.json."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

SEED = Path(__file__).resolve().parent.parent / "data" / "seed_kunden.json"

# nr ist die laufende Nummer hinter "FS-". SQLite vergibt für neue Zeilen
# die höchste vorhandene Nummer plus 1, also geht es nach dem Bestand weiter.
SCHEMA = """
DROP TABLE IF EXISTS auftraege;
DROP TABLE IF EXISTS kunden;
CREATE TABLE kunden (
    kundennummer TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    steuer_id TEXT NOT NULL
);
CREATE TABLE auftraege (
    nr INTEGER PRIMARY KEY,
    kundennummer TEXT NOT NULL REFERENCES kunden,
    referenz TEXT NOT NULL,
    steuer_id TEXT NOT NULL,
    betrag TEXT NOT NULL,
    gemeinsam TEXT NOT NULL,
    steuer_id_partner TEXT NOT NULL,
    gueltig_ab TEXT NOT NULL
);
"""
FELDER = ("kundennummer", "referenz", "steuer_id", "betrag", "gemeinsam", "steuer_id_partner", "gueltig_ab")


@contextmanager
def _verbindung(pfad):
    con = sqlite3.connect(pfad)
    con.row_factory = sqlite3.Row
    try:
        with con:  # Commit bei Erfolg, Rollback bei Fehler
            yield con
    finally:
        con.close()


def _als_dict(zeile):
    return {**zeile, "bestaetigungsnr": f"FS-{zeile['nr']:06d}"}


def init(pfad):
    """Legt die Datenbank beim ersten Start an."""
    if not Path(pfad).exists():
        reset(pfad)


def reset(pfad):
    """Setzt alle Tabellen auf die Ausgangsdaten zurück."""
    kunden = json.loads(SEED.read_text(encoding="utf-8"))
    with _verbindung(pfad) as con:
        con.executescript(SCHEMA)
        for k in kunden:
            con.execute("INSERT INTO kunden VALUES (?, ?, ?)", (k["kundennummer"], k["name"], k["steuer_id"]))
            for a in k["auftraege"]:
                con.execute(
                    "INSERT INTO auftraege VALUES (?, ?, ?, ?, ?, ?, '', ?)",
                    (int(a["bestaetigungsnr"][3:]), k["kundennummer"], a["referenz"], k["steuer_id"],
                     str(a["betrag"]), a["gemeinsam"], a["gueltig_ab"]))


def kunde(pfad, kundennummer):
    with _verbindung(pfad) as con:
        zeile = con.execute("SELECT * FROM kunden WHERE kundennummer = ?", (kundennummer,)).fetchone()
    return dict(zeile) if zeile else None


def auftraege(pfad, kundennummer):
    with _verbindung(pfad) as con:
        zeilen = con.execute("SELECT * FROM auftraege WHERE kundennummer = ? ORDER BY nr", (kundennummer,))
        return [_als_dict(z) for z in zeilen]


def auftrag(pfad, bestaetigungsnr):
    with _verbindung(pfad) as con:
        zeile = con.execute(
            "SELECT * FROM auftraege WHERE printf('FS-%06d', nr) = ?", (bestaetigungsnr,)).fetchone()
    return _als_dict(zeile) if zeile else None


def speichere_auftrag(pfad, daten):
    """Speichert die Eingaben ungeprüft und gibt die Bestätigungsnummer zurück."""
    with _verbindung(pfad) as con:
        cur = con.execute(
            f"INSERT INTO auftraege ({', '.join(FELDER)}) VALUES ({', '.join('?' * len(FELDER))})",
            [daten[f] for f in FELDER])
        return f"FS-{cur.lastrowid:06d}"
