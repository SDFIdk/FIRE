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


def test_hent_punkt(firedb: FireDb):
    p = firedb.hent_punkt("814E9044-1439-5A4E-E053-1A041EACF9E4")
    assert isinstance(p, Punkt)
    k = p.koordinater[0]
    assert isinstance(k, Koordinat)


def test_hent_alle_punkter(firedb: FireDb):
    p = firedb.hent_alle_punkter()
    assert isinstance(p, list)
