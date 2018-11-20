
def test_has_session(firedb):
    assert hasattr(firedb, "session")


def test_hent_alle_punkter(firedb):
    p = firedb.hent_alle_punkter()
    assert isinstance(p, list)

