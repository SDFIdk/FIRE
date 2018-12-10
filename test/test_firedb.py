import datetime
from fireapi.model import *


def test_has_session(firedb):
    assert hasattr(firedb, "session")


def test_hent_alle_punkter(firedb):
    p = firedb.hent_alle_punkter()
    assert isinstance(p, list)


def test_hent_observationer_naer_punkt(firedb):
    # p = firedb.hent_punkt('7C581B4A-5A4C-7F16-E053-1A041EAC3A76')
    p = Punkt(id="7C581B4A-5A4C-7F16-E053-1A041EAC3A76")
    fra = datetime.datetime.utcnow() - datetime.timedelta(weeks=10)
    til = datetime.datetime.utcnow()
    os = firedb.hent_observationer_naer_punkt(p, 100, fra, til)
    assert isinstance(os, list)
