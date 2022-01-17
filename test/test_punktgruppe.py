import fire
from fire.api import FireDb
from fire.api.model import (
    Punkt,
    PunktGruppe,
    EventType,
)


def test_hent_punktgruppe(firedb):
    """Test at vi kan læse punktgruppe fra databasen"""
    punktgruppe = firedb.hent_punktgruppe("Aarhus Nivellementstest")

    assert punktgruppe.jessenpunkt.ident == "RDIO"
    assert punktgruppe.navn == "Aarhus Nivellementstest"

    assert len(punktgruppe.punkter) == 3
    for p in punktgruppe.punkter:
        assert p.ident in ("K-63-19113", "K-63-09933", "K-63-09116")


def test_hent_fra_punkt(firedb):
    """Test at en punktgruppe kan findes via et punkt"""
    punkt = firedb.hent_punkt("RDIO")
    punktgruppe = punkt.punktgrupper[0]
    assert isinstance(punktgruppe, PunktGruppe)


def test_opret_punktgruppe(firedb, sagsevent, punktfabrik):
    """Test at en punktgruppe kan oprettes"""

    punkter = [punktfabrik() for _ in range(3)]

    punktgruppe = PunktGruppe(
        navn=f"Test-{fire.uuid()[0:9]}",
        punkter=punkter,
        jessenpunkt=punktfabrik(),
    )

    sagsevent.eventtype = EventType.PUNKTGRUPPE_MODIFICERET
    sagsevent.punktgrupper = [punktgruppe]
    firedb.indset_sagsevent(sagsevent)


def test_udvid_punktgruppe(firedb, sagseventfabrik, punktgruppe, punkt):
    """Test at en punktgruppe kan oprettes"""

    firedb.session.flush()
    punktgruppenavn = punktgruppe.navn

    # glem at vi allerede har hentet punktgruppen en gang
    del punktgruppe

    punktgruppe = firedb.hent_punktgruppe(punktgruppenavn)
    punktgruppe.punkter.append(punkt)

    sagsevent = sagseventfabrik()
    sagsevent.punktgrupper = [punktgruppe]
    sagsevent.eventtype = EventType.PUNKTGRUPPE_MODIFICERET

    firedb.indset_sagsevent(sagsevent)

    assert len(punktgruppe.punkter) == 6


def test_luk_punktgruppe(firedb, sagsevent, punktgruppe):

    firedb.session.flush()

    assert punktgruppe.sagseventtilid is None
    assert punktgruppe.registreringtil is None

    firedb.luk_punktgruppe(punktgruppe, sagsevent)

    assert punktgruppe.sagseventtilid is not None
    assert punktgruppe.registreringtil is not None
