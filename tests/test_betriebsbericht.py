from datetime import datetime

from monitoring.betriebsbericht import auswerten, bericht


def eintrag(status, typ=None, grund=None):
    return {"Status": status, "ProcessingExceptionType": typ,
            "ProcessingException": {"Reason": grund} if grund else None}


EINTRAEGE = (
    [eintrag("Successful")] * 3
    + [eintrag("Failed", "BusinessException", "LIMIT_EINZEL"),
       eintrag("Failed", "BusinessException", "STEUERID_FORMAT,BETRAG_UNGUELTIG"),
       eintrag("Failed", "ApplicationException", "Timeout"),
       eintrag("Retried", "ApplicationException", "Timeout"),
       eintrag("New")]
)


def test_auswerten_zaehlt_nach_ergebnis():
    assert auswerten(EINTRAEGE) == {
        "verarbeitet": 6, "erfolgreich": 3, "fachlich": 2,
        "codes": {"BETRAG_UNGUELTIG": 1, "LIMIT_EINZEL": 1, "STEUERID_FORMAT": 1},
        "system": 1, "wiederholungen": 1, "offen": 1,
    }


def test_bericht_nennt_jeden_code():
    text = bericht("FSA_Eingang", auswerten(EINTRAEGE), datetime(2026, 11, 11, 6, 0))
    assert text.splitlines()[0] == "Betriebsbericht FSA_Eingang, Stand 11.11.2026 06:00"
    assert "  LIMIT_EINZEL: 1" in text
    assert "Systemausnahmen:      1" in text
