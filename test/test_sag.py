import pytest
from fireapi.model import Sag, Sagsinfo


@pytest.mark.skip(
    reason="Sag cannot be inserted atm because of missing mapping of sagstype"
)
def test_soft_delete(firedb):
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
