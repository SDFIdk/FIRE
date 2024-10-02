from typing import Callable

import pytest
from sqlalchemy.exc import NoResultFound

import fire
from fire.api import FireDb
from fire.api.model import (
    Koordinat,
    Punkt,
    PunktSamling,
    Sagsevent,
    EventType,
)


def test_hent_punktsamling(firedb: FireDb):
    """Test at vi kan læse punktsamling fra databasen"""
    punktsamling = firedb.hent_punktsamling("Aarhus Nivellementstest")

    assert punktsamling.jessenpunkt.ident == "RDIO"
    assert punktsamling.navn == "Aarhus Nivellementstest"

    assert len(punktsamling.punkter) == 4
    for p in punktsamling.punkter:
        assert p.ident in ("RDIO", "K-63-19113", "K-63-09933", "K-63-09116")

    with pytest.raises(NoResultFound):
        firedb.hent_punktsamling("findes ikke")


def test_hent_alle_punktsamlinger(firedb: FireDb):
    p = firedb.hent_alle_punktsamlinger()
    assert isinstance(p, list)


def test_hent_fra_punkt(firedb: FireDb):
    """Test at en punktsamling kan findes via et punkt"""
    punkt = firedb.hent_punkt("RDIO")
    punktsamling = punkt.punktsamlinger[0]

    assert isinstance(punktsamling, PunktSamling)
    assert punktsamling.navn == "Aarhus Nivellementstest"
    assert punktsamling.formål == "Kontrollere stabiliteten af RDIO"


def test_opret_punktsamling(
    firedb: FireDb,
    sagseventfabrik: Callable,
    punktfabrik: Callable,
    koordinat: Koordinat,
):
    """Test at en punktsamling kan oprettes"""
    firedb.session.flush()

    navn = f"Test-{fire.uuid()[0:9]}"
    jessenpunkt = punktfabrik()

    punkter = [
        jessenpunkt,
    ] + [punktfabrik() for _ in range(3)]

    punktsamling = PunktSamling(
        navn=navn,
        formål="Test",
        punkter=punkter,
        jessenpunkt=jessenpunkt,
        jessenkoordinat=koordinat,
    )

    sagsevent = sagseventfabrik()
    sagsevent.eventtype = EventType.PUNKTGRUPPE_MODIFICERET
    sagsevent.punktsamlinger = [punktsamling]
    firedb.indset_sagsevent(sagsevent, commit=False)
    firedb.session.flush()

    del punktsamling

    ps = firedb.hent_punktsamling(navn)

    assert ps.jessenkoordinat == koordinat
    assert ps.jessenpunkt == jessenpunkt

    # rækkefølgen efter udtræk er ikke garanteret at være samme som ved indlæsning
    assert sorted(ps.punkter) == sorted(punkter)

    assert ps.navn == navn
    assert ps.formål == "Test"

    firedb.session.rollback()


def test_udvid_punktsamling(
    firedb: FireDb, sagseventfabrik: Callable, punktsamling: PunktSamling, punkt: Punkt
):
    """Test at en punktsamling kan udvides"""

    firedb.session.flush()
    punktsamlingnavn = punktsamling.navn

    # glem at vi allerede har hentet punktsamlingn en gang
    del punktsamling

    punktsamling = firedb.hent_punktsamling(punktsamlingnavn)
    punktsamling.tilføj_punkter([punkt])

    sagsevent = sagseventfabrik()
    sagsevent.punktsamlinger = [punktsamling]
    sagsevent.eventtype = EventType.PUNKTGRUPPE_MODIFICERET

    firedb.indset_sagsevent(sagsevent, commit=False)
    firedb.session.flush()

    assert len(punktsamling.punkter) == 6

    firedb.session.rollback()


def test_fjern_punkter_fra_punktsamling(
    firedb: FireDb,
    sagseventfabrik: Callable,
    punktsamling: PunktSamling,
    punktfabrik: Callable,
):
    """Test at man kan fjerne punkter fra en punktsamling"""
    firedb.session.flush()

    jessenpunkt = punktsamling.jessenpunkt
    punkter = [p for p in punktsamling.punkter if p != jessenpunkt]
    punkt = punktfabrik()

    # Test at man ikke kan fjerne et punkt som ikke findes i punktsamlingen
    with pytest.raises(ValueError, match="not in list"):
        punktsamling.fjern_punkter([punkt])

    # Test at man ikke kan fjerne jessenpunktet
    with pytest.raises(ValueError, match="jessenpunkt"):
        punktsamling.fjern_punkter([jessenpunkt])

    # Fjern alle andre punkter
    punktsamling.fjern_punkter(punkter)
    sagsevent = sagseventfabrik()
    sagsevent.punktsamlinger = [punktsamling]
    sagsevent.eventtype = EventType.PUNKTGRUPPE_MODIFICERET

    firedb.indset_sagsevent(sagsevent, commit=False)
    firedb.session.flush()

    # Glem punktsamlingen og hent den fra databasen igen
    punktsamlingsnavn = punktsamling.navn
    del punktsamling
    punktsamling = firedb.hent_punktsamling(punktsamlingsnavn)

    # Tjek at der nu kun er ét punkt tilbage, nemlig jessenpunktet.
    assert len(punktsamling.punkter) == 1

    firedb.session.rollback()


def test_luk_punktsamling(
    firedb: FireDb, sagsevent: Sagsevent, punktsamling: PunktSamling
):
    """Test at en punktsamling kan lukkes"""
    firedb.session.flush()

    assert punktsamling.sagseventtilid is None
    assert punktsamling.registreringtil is None

    firedb.luk_punktsamling(punktsamling, sagsevent, commit=False)
    firedb.session.flush()

    assert punktsamling.sagseventtilid is not None
    assert punktsamling.registreringtil is not None

    firedb.session.rollback()
