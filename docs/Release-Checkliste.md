# Release-Checkliste

Vor jedem neuen Bot-Release abhaken:

- [ ] Änderung beschrieben (CHANGELOG)
- [ ] Regeltests grün (Python-Tests und `Tests/RunRuleTests.xaml`)
- [ ] Workflow Analyzer ohne Fehler
- [ ] Lauf im Ordner Musterbank_Test mit Testdaten
- [ ] Ergebnis der Warteschlange geprüft (erwartete Anzahl erfolgreich und fachliche Ausnahmen)
- [ ] Versionsnummer in project.json erhöht
- [ ] Pull Request von einer zweiten Person geprüft (Vier-Augen-Prinzip)
- [ ] Paket veröffentlicht und Prozess in Musterbank_Prod aktualisiert
- [ ] Rückweg festgelegt (vorherige Version bleibt verfügbar)
