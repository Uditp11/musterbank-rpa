"""Betriebsbericht: liest die Einträge einer Orchestrator-Warteschlange und druckt eine kurze Tagesübersicht.

Aufruf:  python -m monitoring.betriebsbericht
Umgebungsvariablen (nie ins Repository schreiben, lokal z. B. in .env):
  UIPATH_URL        https://cloud.uipath.com/<Organisation>/<Tenant>
  UIPATH_TOKEN      Zugriffstoken (Bearer)
  UIPATH_FOLDER_ID  numerische Id des Orchestrator-Ordners
  UIPATH_QUEUE      Name der Warteschlange, Standard FSA_Eingang
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime


def lade_eintraege(url, token, folder_id, queue):
    # Die API liefert höchstens 100 Einträge pro Abfrage, darum seitenweise mit $skip.
    filt = urllib.parse.quote(f"QueueDefinition/Name eq '{queue}'", safe="/'")
    eintraege = []
    while True:
        req = urllib.request.Request(
            f"{url.rstrip('/')}/orchestrator_/odata/QueueItems?$filter={filt}&$top=100&$skip={len(eintraege)}",
            # Ohne eigenen User-Agent lehnt die Cloud Anfragen von urllib mit 403 ab.
            headers={"Authorization": f"Bearer {token}", "X-UIPATH-OrganizationUnitId": str(folder_id),
                     "User-Agent": "musterbank-betriebsbericht"},
        )
        with urllib.request.urlopen(req, timeout=30) as antwort:
            seite = json.load(antwort)["value"]
        eintraege += seite
        if len(seite) < 100:
            return eintraege


def auswerten(eintraege):
    """Zählt die Einträge nach Ergebnis. Ein Eintrag mit Status Retried ist ein früherer Versuch."""
    erfolgreich = fachlich = system = wiederholt = offen = 0
    codes = Counter()
    for e in eintraege:
        status = e.get("Status")
        if status == "Successful":
            erfolgreich += 1
        elif status == "Retried":
            wiederholt += 1
        elif status in ("New", "InProgress"):
            offen += 1
        elif status in ("Failed", "Abandoned"):
            if e.get("ProcessingExceptionType") == "BusinessException":
                fachlich += 1
                grund = (e.get("ProcessingException") or {}).get("Reason") or "OHNE_CODE"
                codes.update(c.strip() for c in grund.split(",") if c.strip())
            else:
                system += 1
    return {
        "verarbeitet": erfolgreich + fachlich + system,
        "erfolgreich": erfolgreich,
        "fachlich": fachlich,
        "codes": dict(sorted(codes.items())),
        "system": system,
        "wiederholungen": wiederholt,
        "offen": offen,
    }


def bericht(queue, zahlen, stand):
    zeilen = [
        f"Betriebsbericht {queue}, Stand {stand:%d.%m.%Y %H:%M}",
        f"Verarbeitet:          {zahlen['verarbeitet']}",
        f"Erfolgreich:          {zahlen['erfolgreich']}",
        f"Fachliche Ausnahmen:  {zahlen['fachlich']}",
    ]
    zeilen += [f"  {code}: {anzahl}" for code, anzahl in zahlen["codes"].items()]
    zeilen += [
        f"Systemausnahmen:      {zahlen['system']}",
        f"Wiederholungen:       {zahlen['wiederholungen']}",
        f"Noch offen:           {zahlen['offen']}",
    ]
    return "\n".join(zeilen)


def main():
    try:
        url, token, folder = (os.environ[k] for k in ("UIPATH_URL", "UIPATH_TOKEN", "UIPATH_FOLDER_ID"))
    except KeyError as fehlt:
        sys.exit(f"Umgebungsvariable fehlt: {fehlt.args[0]}")
    queue = os.environ.get("UIPATH_QUEUE", "FSA_Eingang")
    print(bericht(queue, auswerten(lade_eintraege(url, token, folder, queue)), datetime.now()))


if __name__ == "__main__":
    main()
