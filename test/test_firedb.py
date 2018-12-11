import datetime


def test_has_session(firedb):
    assert hasattr(firedb, "session")


def test_hent_alle_punkter(firedb):
    p = firedb.hent_alle_punkter()
    assert isinstance(p, list)


def test_hent_observationer_naer_punkt(firedb):
    p = firedb.hent_punkt("7CA9F53D-DE26-59C0-E053-1A041EAC5678")
    fra = datetime.datetime.utcnow() - datetime.timedelta(weeks=10)
    til = datetime.datetime.utcnow()
    os = firedb.hent_observationer_naer_punkt(p, 100, fra, til)
    assert isinstance(os, list)
    assert len(os) is 2
    os = firedb.hent_observationer_naer_punkt(p, 1000, fra, til)
    assert len(os) is 4
