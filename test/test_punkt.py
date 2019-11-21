import pytest
import uuid
from fireapi import FireDb
from fireapi.model import (
    Sagsevent,
    Punkt,
    Koordinat,
    GeometriObjekt,
    Point,
    Sag,
    EventType,
)


def test_punkt(firedb: FireDb, punkt: Punkt):
    firedb.session.commit()


def test_indset_punkt(firedb: FireDb, sag: Sag):
    p = Punkt(id=str(uuid.uuid4()))
    go = GeometriObjekt()
    go.geometri = Point([1, 1])
    p.geometriobjekter.append(go)
    firedb.indset_punkt(Sagsevent(sag=sag), p)


def test_indset_punkt_with_invalid_sagsevent_eventtype(firedb: FireDb, sag: Sag):
    p = Punkt(id=str(uuid.uuid4()))
    go = GeometriObjekt()
    go.geometri = Point([1, 1])
    p.geometriobjekter.append(go)
    with pytest.raises(Exception, match="KOMMENTAR"):
        firedb.indset_punkt(Sagsevent(sag=sag, eventtype=EventType.KOMMENTAR), p)


def test_hent_punkt(firedb: FireDb, punkt: Punkt):
    punktid = punkt.id
    firedb.session.commit()  # sørg for at punkt indsættes i databasen
    print(punktid)
    print(punkt)
    p = firedb.hent_punkt(punktid)
    assert isinstance(p, Punkt)
    s = p.sagsevent
    assert isinstance(s, Sagsevent)


def test_hent_alle_punkter(firedb: FireDb):
    p = firedb.hent_alle_punkter()
    assert isinstance(p, list)
