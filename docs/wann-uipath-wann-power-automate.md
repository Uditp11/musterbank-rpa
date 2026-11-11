# Wann UiPath, wann Power Automate

| Kriterium | UiPath | Power Automate |
|---|---|---|
| Alte Anwendungen ohne Schnittstelle (Bildschirm-Automatisierung) | Stärke: bedient Fenster und Webseiten wie ein Mensch | Möglich mit der Desktop-Variante, aber nicht der Schwerpunkt |
| Microsoft-365-Abläufe (Mail, SharePoint, Teams, Freigaben) | Möglich, aber meist mehr Aufwand | Stärke: Anschlüsse sind fertig vorhanden |
| Attended oder unattended | Beides: Roboter läuft am Arbeitsplatz oder ohne Person auf einer Maschine | Beides, je nach Variante (Cloud-Flows oder Desktop-Flows) |
| Warteschlangen und Wiederholungen | Orchestrator-Warteschlangen mit automatischen Wiederholungen und Referenz gegen Doppelverarbeitung | Wiederholungsregeln je Schritt, keine Warteschlange in diesem Sinn |
| Überwachung und Protokolle | Orchestrator zeigt Aufträge, Protokolle und Alarme zentral | Ausführungsverlauf je Flow, Verwaltung über das Microsoft-Admin-Center |
| Lizenz und Kosten | Eigene Lizenz, abhängig von Roboter-Art und Umfang | Oft in Microsoft-365-Lizenzen enthalten, Premium-Funktionen kosten extra |
| Governance und Freigabe | Getrennte Ordner, Rollen, versionierte Pakete | Umgebungen, Richtlinien zum Datenschutz, Freigabe über Lösungen |

## Faustregel

Gibt es eine Schnittstelle und der Ablauf liegt in Microsoft 365, ist Power Automate meist der kürzere Weg. Gibt es nur eine Oberfläche ohne Schnittstelle, braucht man Bildschirm-Automatisierung, und dafür ist UiPath gut geeignet. Bei vielen Einzelfällen mit Wiederholungen und Nachweis hilft eine Warteschlange. Beide Werkzeuge lassen sich kombinieren. Die Tabelle ist eine grobe Orientierung, im Einzelfall zählen Lizenz und interne Vorgaben.

## In diesem Projekt

Der Bot nutzt UiPath, weil das Musterbank Backoffice keine Schnittstelle hat. Eine sinnvolle Ergänzung wäre ein Power-Automate-Flow, der eine Alarm-Mail aus Orchestrator in einen Eintrag in der SharePoint-Liste "Bot-Störungen" umwandelt und eine Nachricht in Teams schickt. Dieser Flow ist nur eine Idee und nicht gebaut.
