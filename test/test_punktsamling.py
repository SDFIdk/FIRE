import pytest
from sqlalchemy.exc import NoResultFound

import fire
from fire.api import FireDb
from fire.api.model import (
    Punkt,
    PunktSamling,
    EventType,
)


def test_hent_punktsamling(firedb):
    """Test at vi kan læse punktsamling fra databasen"""
    punktsamling = firedb.hent_punktsamling("Aarhus Nivellementstest")

    assert punktsamling.jessenpunkt.ident == "RDIO"
    assert punktsamling.navn == "Aarhus Nivellementstest"

    assert len(punktsamling.punkter) == 4
    for p in punktsamling.punkter:
        assert p.ident in ("RDIO", "K-63-19113", "K-63-09933", "K-63-09116")

    with pytest.raises(NoResultFound):
        firedb.hent_punktsamling("findes ikke")


def test_hent_fra_punkt(firedb):
    """Test at en punktsamling kan findes via et punkt"""
    punkt = firedb.hent_punkt("RDIO")
    punktsamling = punkt.punktsamlinger[0]

    assert isinstance(punktsamling, PunktSamling)
    assert punktsamling.navn == "Aarhus Nivellementstest"
    assert punktsamling.formål == "Kontrollere stabiliteten af RDIO"


def test_opret_punktsamling(firedb, sagsevent, punktfabrik, koordinat):
    """Test at en punktsamling kan oprettes"""

    navn = f"Test-{fire.uuid()[0:9]}"
    jessenpunkt = punktfabrik()

    punkter = [jessenpunkt,] + [punktfabrik() for _ in range(3)]

    punktsamling = PunktSamling(
        navn=navn,
        formål="Test",
        punkter=punkter,
        jessenpunkt=jessenpunkt,
        jessenkoordinat=koordinat,
    )

    sagsevent.eventtype = EventType.PUNKTGRUPPE_MODIFICERET
    sagsevent.punktsamlinger = [punktsamling]
    firedb.indset_sagsevent(sagsevent)

    del punktsamling

    ps = firedb.hent_punktsamling(navn)

    assert ps.jessenkoordinat == koordinat
    assert ps.jessenpunkt == jessenpunkt

    # rækkefølgen efter udtræk er ikke garanteret at være samme som ved indlæsning
    assert sorted(ps.punkter) == sorted(punkter)

    assert ps.navn == navn
    assert ps.formål == "Test"


def test_udvid_punktsamling(firedb, sagseventfabrik, punktsamling, punkt):
    """Test at en punktsamling kan oprettes"""

    firedb.session.flush()
    punktsamlingnavn = punktsamling.navn

    # glem at vi allerede har hentet punktsamlingn en gang
    del punktsamling

    punktsamling = firedb.hent_punktsamling(punktsamlingnavn)
    punktsamling.punkter.append(punkt)

    sagsevent = sagseventfabrik()
    sagsevent.punktsamlinger = [punktsamling]
    sagsevent.eventtype = EventType.PUNKTGRUPPE_MODIFICERET

    firedb.indset_sagsevent(sagsevent)

    assert len(punktsamling.punkter) == 6


def test_luk_punktsamling(firedb, sagsevent, punktsamling):
    firedb.session.flush()

    assert punktsamling.sagseventtilid is None
    assert punktsamling.registreringtil is None

    firedb.luk_punktsamling(punktsamling, sagsevent)

    assert punktsamling.sagseventtilid is not None
    assert punktsamling.registreringtil is not None
