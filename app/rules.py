"""Geschäftsregeln für Freistellungsaufträge.

Die Anwendung selbst prüft diese Regeln nicht. Sie beschreiben, was vor der
Erfassung geprüft werden muss, und dienen als Referenz für die Automatisierung.
"""
from collections import Counter

LIMIT_EINZEL = 1000
LIMIT_GEMEINSAM = 2000


def pruefziffer(ziffern10: str) -> int:
    """Prüfziffer der Steuer-ID (ISO/IEC 7064, MOD 11,10) zu den ersten 10 Ziffern."""
    produkt = 10
    for z in ziffern10:
        summe = (int(z) + produkt) % 10 or 10
        produkt = summe * 2 % 11
    return (11 - produkt) % 10


def steuerid_valid(s: str) -> str | None:
    """None, wenn die Steuer-ID gültig ist, sonst der Fehlercode."""
    if len(s) != 11 or not (s.isascii() and s.isdigit()) or s[0] == "0":
        return "STEUERID_FORMAT"
    # Genau eine Ziffer kommt in den ersten 10 Stellen 2- oder 3-mal vor,
    # alle anderen höchstens einmal. Drei gleiche stehen nie direkt hintereinander.
    mehrfach = [(z, n) for z, n in Counter(s[:10]).items() if n > 1]
    if len(mehrfach) != 1:
        return "STEUERID_FORMAT"
    ziffer, anzahl = mehrfach[0]
    if anzahl > 3 or ziffer * 3 in s[:10]:
        return "STEUERID_FORMAT"
    if int(s[10]) != pruefziffer(s[:10]):
        return "STEUERID_PRUEFZIFFER"
    return None


def _betrag(wert) -> int | None:
    """Betrag in ganzen Euro größer 0, sonst None."""
    if isinstance(wert, float) and wert.is_integer():
        wert = int(wert)
    elif isinstance(wert, str) and wert.isascii() and wert.strip().isdigit():
        wert = int(wert)
    if isinstance(wert, int) and not isinstance(wert, bool) and wert > 0:
        return wert
    return None


def pruefe_auftrag(auftrag: dict, bestehende_summe: int) -> list[str]:
    """Alle Fehlercodes eines Auftrags in fester Reihenfolge, leer wenn gültig.

    bestehende_summe: Summe der Aufträge, die der Kunde schon hat.
    KUNDE_UNBEKANNT wird hier nicht geprüft, das entscheidet die Kundensuche.
    """
    codes = []
    code = steuerid_valid(str(auftrag.get("Steuer_ID") or "").strip())
    if code:
        codes.append(code)

    betrag = _betrag(auftrag.get("Betrag"))
    if betrag is None:
        codes.append("BETRAG_UNGUELTIG")

    gemeinsam = str(auftrag.get("Gemeinsam") or "").strip().lower() == "ja"
    if gemeinsam:
        partner = str(auftrag.get("Steuer_ID_Partner") or "").strip()
        if not partner:
            codes.append("PARTNER_FEHLT")
        elif steuerid_valid(partner):
            codes.append("PARTNER_STEUERID")

    if betrag is not None:
        limit = LIMIT_GEMEINSAM if gemeinsam else LIMIT_EINZEL
        if betrag > limit:
            codes.append("LIMIT_GEMEINSAM" if gemeinsam else "LIMIT_EINZEL")
        elif bestehende_summe + betrag > limit:
            codes.append("LIMIT_GESAMT")
    return codes
