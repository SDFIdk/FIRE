import uuid
import datetime as dt

import pytest

from fire.api import FireDb
from fire.api.model import (
    Koordinat,
    Artskode,
    Srid,
    Punkt,
    Sag,
    Sagsevent,
    EventType,
)


def test_koordinat(firedb: FireDb, koordinat: Koordinat):
    firedb.session.commit()


def test_artskode(firedb: FireDb, koordinat: Koordinat):
    koordinat.artskode = Artskode.TRANSFORMERET
    firedb.session.commit()


def test_afregistrering_af_koordinat(
    firedb: FireDb, sag: Sag, srid: Srid, punkt: Punkt
):
    """
    Database triggeren BID#KOORDINAT sætter registreringtil og sagseventtilid ved
    indsættelse af ny koordinat. Tjek at triggeren virker.
    """

    se1 = Sagsevent(
        id=str(uuid.uuid4()), sag=sag, eventtype=EventType.KOORDINAT_BEREGNET
    )
    se1.koordinater = [
        Koordinat(
            srid=srid,
            punkt=punkt,
            t=dt.datetime(2020, 5, 13, 8, 0),
            x=0,
            y=0,
            z=0,
            sx=0,
            sy=0,
            sz=0,
        )
    ]
    firedb.session.add(se1)
    firedb.session.commit()

    se2 = Sagsevent(
        id=str(uuid.uuid4()), sag=sag, eventtype=EventType.KOORDINAT_BEREGNET
    )
    se2.koordinater = [
        Koordinat(
            srid=srid,
            punkt=punkt,
            t=dt.datetime(2020, 5, 13, 9, 45),
            x=1,
            y=1,
            z=1,
            sx=1,
            sy=1,
            sz=1,
        )
    ]
    firedb.session.add(se2)
    firedb.session.commit()

    p = firedb.hent_punkt(punkt.id)

    assert len(p.koordinater) == 2

    assert p.koordinater[0].srid.sridid == srid.sridid
    assert p.koordinater[1].srid.sridid == srid.sridid

    assert p.koordinater[0].registreringtil == p.koordinater[1].registreringfra
    assert p.koordinater[0].sagseventtilid == p.koordinater[1].sagseventfraid


def test_luk_koordinat(firedb: FireDb, koordinat: Koordinat, sagsevent: Sagsevent):
    firedb.session.commit()
    assert koordinat.registreringtil is None
    assert koordinat.sagsevent.eventtype == EventType.KOORDINAT_BEREGNET

    firedb.luk_koordinat(koordinat, sagsevent)
    assert koordinat.registreringtil is not None
    assert koordinat.sagsevent.eventtype == EventType.KOORDINAT_NEDLAGT

    with pytest.raises(TypeError):
        firedb.luk_koordinat(firedb)
