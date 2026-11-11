# Änderungsnotizen

## 1.0.0 (2026-11-11)

- Dispatcher: liest die Excel-Liste und legt je Auftrag einen Eintrag in die Warteschlange `FSA_Eingang`. Doppelte Referenzen werden übersprungen.
- Performer (REFramework): sucht den Kunden, prüft die Geschäftsregeln, erfasst gültige Aufträge und speichert die Bestätigungsnummer am Eintrag.
- Regeltests in UiPath mit denselben Fällen wie die Python-Tests.
- Betriebsbericht aus der Orchestrator-Warteschlange.
- Bekannte Lücke: Version 1.0.0 prüft nicht, ob eine Referenz schon erfasst ist.

## 0.1.0 (2026-11-11)

- Geschäftsregeln für Freistellungsaufträge, mit Tests
- Testdaten-Generator: 30 Aufträge, davon 6 fachlich ungültig
- Musterbank Backoffice (fiktive Demo-Anwendung) mit Fehlerschaltern: `APP_VERSION=2` und `SLOW_CONFIRM=1`
- Prozessbeschreibung
- Automatische Tests bei jedem Push
