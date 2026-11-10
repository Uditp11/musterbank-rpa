import pytest
from app.rules import steuerid_valid, pruefe_auftrag


@pytest.mark.parametrize("sid", [
    "86095742719", "47036892816", "65929970489", "57549285017", "25768131411",
    "10234567960",   # Pruefziffer 0
])
def test_valid_ids(sid):
    assert steuerid_valid(sid) is None


@pytest.mark.parametrize("sid,code", [
    ("86095742718", "STEUERID_PRUEFZIFFER"),
    ("8609574271", "STEUERID_FORMAT"),
    ("860957427190", "STEUERID_FORMAT"),
    ("06095742719", "STEUERID_FORMAT"),
    ("8609574271a", "STEUERID_FORMAT"),
    ("", "STEUERID_FORMAT"),
    ("12345678903", "STEUERID_FORMAT"),   # keine Ziffer doppelt
    ("11123456789", "STEUERID_FORMAT"),   # Ziffer dreimal direkt hintereinander
    ("11223456789", "STEUERID_FORMAT"),   # zwei Ziffern doppelt
    ("11112345678", "STEUERID_FORMAT"),   # Ziffer viermal
])
def test_invalid_ids(sid, code):
    assert steuerid_valid(sid) == code


def base(**kw):
    a = {"Steuer_ID": "86095742719", "Betrag": 800, "Gemeinsam": "nein", "Steuer_ID_Partner": ""}
    a.update(kw)
    return a


def joint(**kw):
    return base(**{"Gemeinsam": "ja", "Steuer_ID_Partner": "47036892816", **kw})


def test_valid_single():
    assert pruefe_auftrag(base(), 0) == []


def test_limit_einzel():
    assert pruefe_auftrag(base(Betrag=1200), 0) == ["LIMIT_EINZEL"]


def test_einzel_genau_am_limit():
    assert pruefe_auftrag(base(Betrag=1000), 0) == []


def test_limit_gesamt():
    assert pruefe_auftrag(base(Betrag=500), 600) == ["LIMIT_GESAMT"]


def test_gesamt_genau_am_limit():
    assert pruefe_auftrag(base(Betrag=400), 600) == []


def test_limit_gesamt_nur_wenn_einzellimit_passt():
    assert pruefe_auftrag(base(Betrag=1200), 600) == ["LIMIT_EINZEL"]


def test_joint_ok():
    assert pruefe_auftrag(joint(Betrag=2000), 0) == []


def test_joint_over():
    assert pruefe_auftrag(joint(Betrag=2500), 0) == ["LIMIT_GEMEINSAM"]


def test_joint_limit_gesamt():
    assert pruefe_auftrag(joint(Betrag=500), 1600) == ["LIMIT_GESAMT"]


def test_partner_missing():
    assert pruefe_auftrag(base(Gemeinsam="ja"), 0) == ["PARTNER_FEHLT"]


@pytest.mark.parametrize("partner", ["47036892817", "4703689281", "11123456789"])
def test_partner_steuerid(partner):
    assert pruefe_auftrag(joint(Steuer_ID_Partner=partner), 0) == ["PARTNER_STEUERID"]


def test_partner_wird_bei_einzelauftrag_nicht_geprueft():
    assert pruefe_auftrag(base(Steuer_ID_Partner="123"), 0) == []


@pytest.mark.parametrize("betrag", [0, -100, 800.5, "800,00", "abc", "", None, True])
def test_betrag_invalid(betrag):
    assert pruefe_auftrag(base(Betrag=betrag), 0) == ["BETRAG_UNGUELTIG"]


@pytest.mark.parametrize("betrag", [800, 800.0, "800"])
def test_betrag_ganze_euro(betrag):
    assert pruefe_auftrag(base(Betrag=betrag), 0) == []


def test_eigene_steuerid_ungueltig():
    assert pruefe_auftrag(base(Steuer_ID="86095742718"), 0) == ["STEUERID_PRUEFZIFFER"]
    assert pruefe_auftrag(base(Steuer_ID="123"), 0) == ["STEUERID_FORMAT"]


def test_alle_codes_in_fester_reihenfolge():
    auftrag = base(Steuer_ID="86095742718", Betrag=2500, Gemeinsam="ja")
    assert pruefe_auftrag(auftrag, 0) == ["STEUERID_PRUEFZIFFER", "PARTNER_FEHLT", "LIMIT_GEMEINSAM"]
    auftrag = base(Steuer_ID="123", Betrag=0, Gemeinsam="ja", Steuer_ID_Partner="1")
    assert pruefe_auftrag(auftrag, 0) == ["STEUERID_FORMAT", "BETRAG_UNGUELTIG", "PARTNER_STEUERID"]
