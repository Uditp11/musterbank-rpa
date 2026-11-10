import json
from collections import Counter
from pathlib import Path

from openpyxl import load_workbook

from app.rules import pruefe_auftrag, steuerid_valid
from data.generate import SPALTEN, batch2, generate, schreibe

DATA = Path(__file__).parent.parent / "data"
UNGUELTIG = {"KUNDE_UNBEKANNT", "STEUERID_PRUEFZIFFER", "LIMIT_EINZEL",
             "LIMIT_GEMEINSAM", "LIMIT_GESAMT", "PARTNER_FEHLT"}


def fehlercodes(auftrag, kunden):
    """Erst die Kundenliste, dann die Geschäftsregeln (wie in der Verarbeitung)."""
    kunde = next((k for k in kunden if k["kundennummer"] == auftrag["Kundennummer"]), None)
    if kunde is None:
        return ["KUNDE_UNBEKANNT"]
    summe = sum(a["betrag"] for a in kunde["auftraege"])
    return pruefe_auftrag(auftrag, summe)


def zeilen(datei):
    ws = load_workbook(datei)["Eingang"]
    kopf, *rest = ws.iter_rows(values_only=True)
    # leere Zelle (kein Partner) kommt als None zurück
    return list(kopf), [dict(zip(kopf, ("" if v is None else v for v in z))) for z in rest]


def test_30_auftraege_mit_allen_spalten():
    _, auftraege = generate()
    assert len(auftraege) == 30
    assert all(list(a) == SPALTEN for a in auftraege)
    assert SPALTEN == ["Auftrags_ID", "Kundennummer", "Name", "Steuer_ID", "Betrag",
                       "Gemeinsam", "Steuer_ID_Partner", "Gueltig_ab"]


def test_genau_6_ungueltige_je_ein_code():
    kunden, auftraege = generate()
    codes = [fehlercodes(a, kunden) for a in auftraege]
    assert sum(1 for c in codes if not c) == 24
    assert all(len(c) == 1 for c in codes if c)
    assert Counter(c[0] for c in codes if c) == Counter(UNGUELTIG)


def test_gueltige_steuer_ids():
    kunden, auftraege = generate()
    assert all(steuerid_valid(k["steuer_id"]) is None for k in kunden)
    for a in auftraege:
        if not fehlercodes(a, kunden):
            assert steuerid_valid(a["Steuer_ID"]) is None
            if a["Gemeinsam"] == "ja":
                assert steuerid_valid(a["Steuer_ID_Partner"]) is None


def test_gleicher_seed_gleiche_daten():
    assert generate(42) == generate(42)
    assert batch2(42) == batch2(42)
    assert generate(42) != generate(7)


def test_auftrags_ids_und_kundennummern_eindeutig():
    kunden, auftraege = generate()
    alle = auftraege + batch2()
    assert len({a["Auftrags_ID"] for a in alle}) == len(alle) == 40
    assert len({k["kundennummer"] for k in kunden}) == len(kunden)
    assert len({k["name"] for k in kunden}) == len(kunden)
    # Jeder Kunde kommt höchstens einmal vor, damit kein Auftrag das Limit
    # eines anderen Auftrags verbraucht.
    assert len({a["Kundennummer"] for a in alle}) == len(alle)


def test_mindestens_4_kunden_mit_bestehenden_auftraegen():
    kunden, _ = generate()
    assert sum(1 for k in kunden if k["auftraege"]) >= 4
    nummern = [a["bestaetigungsnr"] for k in kunden for a in k["auftraege"]]
    assert len(set(nummern)) == len(nummern)
    # Die Anwendung zählt nach dem höchsten Bestand weiter: nächste Nummer FS-000123.
    assert max(nummern) == "FS-000122"


def test_k10001_ist_frei_fuer_demo():
    kunden, auftraege = generate()
    k = kunden[0]
    assert k["kundennummer"] == "K10001"
    assert k["auftraege"] == []
    assert steuerid_valid(k["steuer_id"]) is None
    assert "K10001" not in {a["Kundennummer"] for a in auftraege + batch2()}
    demo = {"Steuer_ID": k["steuer_id"], "Betrag": 800, "Gemeinsam": "nein", "Steuer_ID_Partner": ""}
    assert pruefe_auftrag(demo, 0) == []


def test_batch2_zehn_gueltige_einzelauftraege():
    kunden, _ = generate()
    auftraege = batch2()
    assert len(auftraege) == 10
    assert all(fehlercodes(a, kunden) == [] for a in auftraege)
    assert all(a["Gemeinsam"] == "nein" for a in auftraege)


def test_excel_batch1_ids_als_text_betrag_als_zahl(tmp_path):
    schreibe(tmp_path)
    kopf, rows = zeilen(tmp_path / "Eingang_Batch1.xlsx")
    assert kopf == SPALTEN
    assert rows == generate()[1]
    for r in rows:
        assert isinstance(r["Steuer_ID"], str) and isinstance(r["Kundennummer"], str)
        assert isinstance(r["Betrag"], int)
        assert r["Gueltig_ab"] == "01.01.2027"


def test_excel_batch2_betrag_als_text_im_deutschen_format(tmp_path):
    schreibe(tmp_path)
    kopf, rows = zeilen(tmp_path / "Eingang_Batch2_de_format.xlsx")
    assert kopf == SPALTEN
    assert [r["Betrag"] for r in rows] == [f"{a['Betrag']},00" for a in batch2()]
    assert [r["Auftrags_ID"] for r in rows] == [a["Auftrags_ID"] for a in batch2()]


def test_dateien_im_repo_passen_zum_generator(tmp_path):
    schreibe(tmp_path)
    kunden = json.loads((DATA / "seed_kunden.json").read_text(encoding="utf-8"))
    assert kunden == generate()[0]
    for name in ("Eingang_Batch1.xlsx", "Eingang_Batch2_de_format.xlsx"):
        assert zeilen(DATA / name) == zeilen(tmp_path / name)
