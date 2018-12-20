import pytest
from fireapi import FireDb
from fireapi.model import Sag, Sagsinfo


@pytest.mark.skip(
    reason="Sag cannot be inserted atm because of missing mapping of sagstype"
)
def test_soft_delete(firedb: FireDb):
    s0 = Sag(id="xxx")
    si0 = Sagsinfo(sag=s0, aktiv="true", behandler="yyy")
    firedb.session.add(si0)

    # s0 = Sag(id="xxx", behandler="yyy")
    firedb.session.add(s0)
    firedb.session.commit()

    s1 = firedb.session.query(Sag).filter(Sag.id == s0.id).one()
    assert s1 is s0
    assert s1.registreringtil is None

    firedb.session.delete(s0)
    firedb.session.commit()

    s2 = firedb.session.query(Sag).filter(Sag.id == s0.id).one()
    assert s0 is s1 is s2
    assert s2.registreringtil is not None


def test_hent_sag(firedb: FireDb, sag: Sag):
    s = firedb.hent_sag(sag.id)
    assert s.id is sag.id


def test_hent_alle_sager(firedb: FireDb):
    ss = firedb.hent_alle_sager()
    assert len(ss) > 1


def test_indset_sag(firedb: FireDb, guid):
    sagsinfo = Sagsinfo(aktiv="true", behandler="test")
    sag = Sag(id=guid, sagsinfos=[sagsinfo])
    firedb.indset_sag(sag)
