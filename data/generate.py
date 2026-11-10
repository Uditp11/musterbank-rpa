"""Erzeugt die synthetischen Testdaten: Kundenstamm und zwei Eingangsdateien.

Aufruf im Projektordner: python -m data.generate  (oder: python data/generate.py)
Alle Namen, Steuer-IDs und Aufträge sind frei erfunden.
"""
import json
import random
import sys
from pathlib import Path

from openpyxl import Workbook

if not __package__:  # direkter Aufruf als Skript: Projektordner importierbar machen
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.rules import pruefziffer, steuerid_valid  # noqa: E402

DATA = Path(__file__).resolve().parent
SPALTEN = ["Auftrags_ID", "Kundennummer", "Name", "Steuer_ID", "Betrag",
           "Gemeinsam", "Steuer_ID_Partner", "Gueltig_ab"]
GUELTIG_AB = "01.01.2027"

FESTE_NAMEN = ["Erika Beispiel", "Max Mustermann", "Lena Testfrau", "Jonas Probe", "Mia Fiktiv"]
VORNAMEN = ["Anna", "Ben", "Clara", "David", "Emma", "Felix", "Greta", "Hannes", "Ida", "Jakob",
            "Karla", "Leon"]
NACHNAMEN = ["Beispiel", "Muster", "Probe", "Fiktiv", "Platzhalter", "Erfunden", "Vorlage", "Testfall"]

# Bestehende Aufträge (Betrag, Gemeinsam) und der neue Auftrag (Betrag, Gemeinsam)
# für die Kunden, die schon Aufträge haben.
MIT_BESTAND = [
    ([(600, "nein")], (500, "nein")),                 # LIMIT_GESAMT: 600 + 500 > 1000
    ([(300, "nein")], (400, "nein")),                 # gültig
    ([(200, "nein"), (250, "nein")], (500, "nein")),  # gültig
    ([(500, "nein")], (500, "nein")),                 # gültig, genau am Limit
    ([(1200, "ja")], (800, "ja")),                    # gültig, genau am Limit
]
NAECHSTE_BESTAETIGUNGSNR = 123  # die Anwendung zählt nach dem Bestand hier weiter


def _steuer_id(rng):
    """Zufällige gültige Steuer-ID: neun verschiedene Ziffern, eine davon doppelt."""
    while True:
        ziffern = rng.sample("0123456789", 9)
        ziffern.insert(rng.randrange(10), rng.choice(ziffern))
        sid = "".join(ziffern)
        sid += str(pruefziffer(sid))
        if steuerid_valid(sid) is None:  # verwirft z.B. eine führende 0
            return sid


def _auftrag(kunde, betrag, gemeinsam="nein", partner=""):
    return {"Auftrags_ID": "", "Kundennummer": kunde["kundennummer"], "Name": kunde["name"],
            "Steuer_ID": kunde["steuer_id"], "Betrag": betrag, "Gemeinsam": gemeinsam,
            "Steuer_ID_Partner": partner, "Gueltig_ab": GUELTIG_AB}


def _nummeriere(auftraege, start):
    for i, a in enumerate(auftraege, start):
        a["Auftrags_ID"] = f"FSA-2026-{i:04d}"
    return auftraege


def generate(seed: int = 42) -> tuple[list[dict], list[dict]]:
    """Kundenstamm (40 Kunden) und die 30 Aufträge der ersten Eingangsdatei.

    K10001 bleibt ohne Auftrag (frei für manuelle Demos), K10002 bis K10030
    kommen in Batch 1 je einmal vor, K10031 bis K10040 in Batch 2.
    """
    rng = random.Random(seed)
    frei = [f"{v} {n}" for v in VORNAMEN for n in NACHNAMEN if f"{v} {n}" not in FESTE_NAMEN]
    namen = FESTE_NAMEN + rng.sample(frei, 35)
    kunden = [{"kundennummer": f"K{10001 + i}", "name": name, "steuer_id": _steuer_id(rng), "auftraege": []}
              for i, name in enumerate(namen)]

    rest = kunden[1:30]
    rng.shuffle(rest)
    auftraege = []

    # Kunden mit bestehenden Aufträgen (damit LIMIT_GESAMT vorkommen kann)
    nr = NAECHSTE_BESTAETIGUNGSNR - sum(len(bestand) for bestand, _ in MIT_BESTAND)
    for bestand, (betrag, gemeinsam) in MIT_BESTAND:
        kunde = rest.pop()
        for alt_betrag, alt_gemeinsam in bestand:
            kunde["auftraege"].append({
                "bestaetigungsnr": f"FS-{nr:06d}", "referenz": f"FSA-2025-{rng.randint(1, 999):04d}",
                "betrag": alt_betrag, "gemeinsam": alt_gemeinsam, "gueltig_ab": "01.01.2026"})
            nr += 1
        partner = _steuer_id(rng) if gemeinsam == "ja" else ""
        auftraege.append(_auftrag(kunde, betrag, gemeinsam, partner))

    # Je ein fachlich ungültiger Fall pro Fehlercode (LIMIT_GESAMT steht oben)
    falsch = _auftrag(rest.pop(), 800)
    sid = falsch["Steuer_ID"]
    falsch["Steuer_ID"] = sid[:10] + str((int(sid[10]) + rng.randint(1, 9)) % 10)  # STEUERID_PRUEFZIFFER
    auftraege += [
        falsch,
        _auftrag(rest.pop(), 1200),                                  # LIMIT_EINZEL
        _auftrag(rest.pop(), 2500, "ja", _steuer_id(rng)),           # LIMIT_GEMEINSAM
        _auftrag(rest.pop(), 1600, "ja"),                            # PARTNER_FEHLT
        _auftrag({"kundennummer": "K99999", "name": "Otto Unbekannt",
                  "steuer_id": _steuer_id(rng)}, 800),               # KUNDE_UNBEKANNT
    ]

    # Die übrigen Kunden: gültige Aufträge, etwa jeder vierte gemeinsam
    for kunde in rest:
        if rng.random() < 0.25:
            auftraege.append(_auftrag(kunde, rng.randrange(1100, 2001, 100), "ja", _steuer_id(rng)))
        else:
            auftraege.append(_auftrag(kunde, rng.randrange(100, 1001, 50)))

    rng.shuffle(auftraege)
    return kunden, _nummeriere(auftraege, 1)


def batch2(seed: int = 42) -> list[dict]:
    """Zweite Lieferung: 10 gültige Einzelaufträge für K10031 bis K10040."""
    kunden, _ = generate(seed)
    rng = random.Random(seed + 1)
    return _nummeriere([_auftrag(k, rng.randrange(100, 1001, 50)) for k in kunden[30:]], 31)


def _excel(datei, auftraege):
    wb = Workbook()
    ws = wb.active
    ws.title = "Eingang"
    ws.append(SPALTEN)
    for a in auftraege:
        ws.append([a[s] for s in SPALTEN])
    wb.save(datei)


def schreibe(ziel: Path = DATA, seed: int = 42) -> None:
    """Schreibt seed_kunden.json und die beiden Eingangsdateien nach ziel."""
    ziel = Path(ziel)
    kunden, auftraege = generate(seed)
    (ziel / "seed_kunden.json").write_text(
        json.dumps(kunden, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    # Batch 1: Nummern als Text, Betrag als Zahl
    _excel(ziel / "Eingang_Batch1.xlsx", auftraege)
    # Batch 2: Betrag als Text im deutschen Format, z.B. "800,00"
    _excel(ziel / "Eingang_Batch2_de_format.xlsx",
           [{**a, "Betrag": f"{a['Betrag']},00"} for a in batch2(seed)])


if __name__ == "__main__":
    schreibe()
    print(f"Testdaten geschrieben nach {DATA.name}/")
