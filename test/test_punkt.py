from typing import List
from itertools import chain

import pytest

from fire.api import FireDb
from fire.api.model import (
    Sagsevent,
    Punkt,
    Observation,
    Koordinat,
    PunktInformation,
    PunktInformationType,
    GeometriObjekt,
    Point,
    Sag,
    EventType,
)


def test_punkt(firedb: FireDb, punkt: Punkt):
    firedb.session.commit()


def test_indset_punkt(firedb: FireDb, sag: Sag):
    p = Punkt()
    go = GeometriObjekt()
    go.geometri = Point([1, 1])
    p.geometriobjekter.append(go)
    firedb.indset_punkt(Sagsevent(sag=sag), p)


def test_indset_punkt_with_invalid_sagsevent_eventtype(firedb: FireDb, sag: Sag):
    p = Punkt()
    go = GeometriObjekt()
    go.geometri = Point([1, 1])
    p.geometriobjekter.append(go)
    with pytest.raises(Exception, match="KOMMENTAR"):
        firedb.indset_punkt(Sagsevent(sag=sag, eventtype=EventType.KOMMENTAR), p)


def test_hent_punkt(firedb: FireDb, punkt: Punkt):
    firedb.session.commit()  # sørg for at punkt indsættes i databasen
    punktid = punkt.id
    print(punktid)
    print(punkt)
    p = firedb.hent_punkt(punktid)
    assert isinstance(p, Punkt)
    s = p.sagsevent
    assert isinstance(s, Sagsevent)


def test_hent_alle_punkter(firedb: FireDb):
    p = firedb.hent_alle_punkter()
    assert isinstance(p, list)


def test_luk_punkt(
    firedb: FireDb,
    punkt: Punkt,
    sagsevent: Sagsevent,
    observationer: List[Observation],
    koordinat: Koordinat,
    punktinformationtype: PunktInformationType,
):
    # byg et punkt der har tilknyttet geometri, koordinat,
    # punktinfo og observationer
    geometri = GeometriObjekt(
        punkt=punkt, geometri=Point([10, 55]), sagsevent=sagsevent
    )
    firedb.session.add(geometri)
    observationer[0].opstillingspunkt = punkt
    observationer[1].sigtepunkt = punkt
    koordinat.punkt = punkt
    punkt.punktinformationer = [
        PunktInformation(infotype=punktinformationtype, sagsevent=sagsevent)
    ]
    firedb.session.commit()

    firedb.luk_punkt(punkt, sagsevent)
    assert punkt.registreringtil is not None
    assert punkt.sagsevent.eventtype == EventType.PUNKT_NEDLAGT
    assert geometri.registreringtil is not None
    assert geometri.sagsevent.eventtype == EventType.PUNKT_NEDLAGT

    for koordinat in punkt.koordinater:
        assert koordinat.registreringtil is not None
        assert koordinat.sagsevent.eventtype == EventType.PUNKT_NEDLAGT

    for punktinfo in punkt.punktinformationer:
        assert punktinfo.registreringtil is not None
        assert punktinfo.sagsevent.eventtype == EventType.PUNKT_NEDLAGT

    for observation in chain(punkt.observationer_fra, punkt.observationer_til):
        assert observation.registreringtil is not None
        assert observation.sagsevent.eventtype == EventType.PUNKT_NEDLAGT

    with pytest.raises(TypeError):
        firedb.luk_punkt(999)
