# Prozessbeschreibung: Freistellungsaufträge

Alle Daten und Kunden sind erfunden. Die Anwendung "Musterbank Backoffice" ist eine Demo, keine echte Bank. Der UiPath-Bot ist in Arbeit. Heute gibt es nur den Python-Teil: Regeln, Testdaten, Web-App und Tests.

## Ziel

Freistellungsaufträge aus einer Excel-Liste sollen schnell, einheitlich und nachvollziehbar erfasst werden. Gültige Aufträge trägt künftig ein Bot in die Web-App ein. Ungültige Aufträge gehen mit einem klaren Fehlercode an eine Person.

## Auslöser

Die Fachabteilung schickt eine Excel-Datei mit neuen Freistellungsaufträgen. Der Lauf startet von Hand, zum Beispiel einmal pro Tag.

## Eingabe

Excel-Datei, Blatt "Eingang", eine Zeile pro Auftrag:

| Spalte | Typ | Beispiel |
|---|---|---|
| Auftrags_ID | Text | FSA-2026-0001 |
| Kundennummer | Text | K10001 |
| Name | Text | Erika Beispiel |
| Steuer_ID | Text (11 Ziffern) | 86095742719 |
| Betrag | ganze Euro | 800 |
| Gemeinsam | "ja" oder "nein" | nein |
| Steuer_ID_Partner | Text, nur bei gemeinsamem Auftrag | (leer) |
| Gueltig_ab | Datum | 01.01.2027 |

## Schritte

| Schritt | Bisher manuell | Künftig durch den Bot |
|---|---|---|
| 1 | Excel öffnen, Zeile lesen | Dispatcher legt jede Zeile als Eintrag in die Warteschlange `FSA_Eingang` |
| 2 | Regeln im Kopf prüfen | Performer prüft die Geschäftsregeln |
| 3 | Kunden in der Web-App suchen | Performer sucht die Kundennummer |
| 4 | Bestehende Aufträge zusammenrechnen | Performer liest die Summe aus der Kundenseite |
| 5 | Formular von Hand ausfüllen und speichern | Performer füllt das Formular aus und speichert |
| 6 | Bestätigungsnummer notieren | Performer liest die Bestätigungsnummer und speichert sie am Eintrag |
| 7 | Fehlerfälle per Mail melden | Fehlerfälle erscheinen mit Code in Orchestrator |

## Geschäftsregeln

Ein Auftrag kann mehrere Fehlercodes haben. Die Prüfung läuft in dieser Reihenfolge:

| Nr. | Code | Bedeutung |
|---|---|---|
| 1 | KUNDE_UNBEKANNT | Die Kundennummer gibt es in der App nicht. |
| 2 | STEUERID_FORMAT | Die Steuer-ID hat nicht genau 11 Ziffern oder die Ziffernregel ist verletzt. |
| 3 | STEUERID_PRUEFZIFFER | Die Prüfziffer der Steuer-ID stimmt nicht. |
| 4 | BETRAG_UNGUELTIG | Der Betrag ist keine ganze Zahl größer als 0. |
| 5 | PARTNER_FEHLT | Der Auftrag ist gemeinsam, aber die Steuer-ID des Partners fehlt. |
| 6 | PARTNER_STEUERID | Die Steuer-ID des Partners ist falsch (Format oder Prüfziffer). |
| 7 | LIMIT_EINZEL | Einzelauftrag über 1.000 EUR. |
| 8 | LIMIT_GEMEINSAM | Gemeinsamer Auftrag über 2.000 EUR. |
| 9 | LIMIT_GESAMT | Bestehende Aufträge plus neuer Betrag liegen über dem Limit des Kunden. Dieser Code wird nur geprüft, wenn das Einzellimit eingehalten ist. |

## Ausnahmen

| Art | Beispiel | Was passiert | Wer bekommt sie |
|---|---|---|---|
| Fachliche Ausnahme | Regel verletzt, zum Beispiel LIMIT_EINZEL | Kein neuer Versuch. Der Eintrag wird mit den Codes abgeschlossen. | Eine Person in der Fachabteilung klärt den Fall |
| Systemausnahme | App antwortet nicht, Button nicht gefunden | Der Eintrag wird automatisch wiederholt, höchstens zweimal. | Das RPA-Team, wenn es nach den Wiederholungen weiter fehlschlägt |

## Ausgabe

- Neue Freistellungsaufträge in der Web-App, jeweils mit Bestätigungsnummer.
- Warteschlange in Orchestrator mit Status je Auftrag: erfolgreich, fachliche Ausnahme oder Systemausnahme.
- Protokoll des Laufs mit Fehlercodes.

## Kennzahlen

- Aufträge pro Lauf: Anzahl der Zeilen im Eingang.
- Ausnahmequote: fachliche Ausnahmen geteilt durch alle Aufträge. Systemausnahmen werden getrennt gezählt.
- Durchlaufzeit: Zeit von Start des Laufs bis zum letzten abgeschlossenen Eintrag.

## Rollen

- Fachabteilung: liefert die Excel-Liste und klärt fachliche Ausnahmen.
- RPA-Team: betreibt den Bot, behebt Systemausnahmen und pflegt Regeln und Releases.
- Freigabe nach Vier-Augen-Prinzip: Jede Änderung am Bot oder an den Regeln prüft eine zweite Person im Pull Request, bevor sie live geht.
