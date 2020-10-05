import datetime as dt

import pytest
from sqlalchemy.exc import DatabaseError

from fire.api import FireDb
from fire.api.model import (
    Srid,
    Sag,
    Sagsinfo,
    Sagsevent,
    SagseventInfo,
    EventType,
    Punkt,
    Koordinat,
    PunktInformation,
    PunktInformationType,
    Boolean,
)


def test_afregistrering_koordinat(firedb: FireDb, sag: Sag, punkt: Punkt, srid: Srid):
    """
    Test trigger BID#KOORDINAT - Automatisk afrestrering af tidligere koordinat.
    """
    k1 = Koordinat(
        punkt=punkt,
        srid=srid,
        x=0,
        y=0,
        z=0,
        sx=0,
        sy=0,
        sz=0,
        t=dt.datetime(2020, 9, 22, 13, 37),
    )
    se = Sagsevent(sag=sag, eventtype=EventType.KOORDINAT_BEREGNET)
    se.koordinater = [k1]
    firedb.session.add(se)

    k2 = Koordinat(
        punkt=punkt,
        srid=srid,
        x=0.1,
        y=0,
        z=0,
        sx=0,
        sy=0,
        sz=0,
        t=dt.datetime(2020, 9, 22, 13, 40),
    )
    se = Sagsevent(sag=sag, eventtype=EventType.KOORDINAT_BEREGNET)
    se.koordinater = [k2]
    firedb.session.add(se)
    firedb.session.commit()

    assert k1.registreringtil == k2.registreringfra
    assert k1.sagseventtilid == k2.sagseventfraid
    assert k2.registreringtil is None
    assert k2.sagseventtilid is None


def test_indlæsning_af_lukket_koordinat(firedb: FireDb, koordinat: Koordinat):
    """
    Test trigger BID#KOORDINAT.

    Direkte indlæsning af en lukket koordinat er ikke tilladt, tjek at databasen
    brokker sig over det.
    """
    koordinat._registreringtil = dt.datetime(2020, 9, 22, 13, 37)
    koordinat._registreringfra = dt.datetime(2020, 9, 22, 13, 37)
    firedb.session.add(koordinat)

    with pytest.raises(DatabaseError):
        firedb.session.commit()

    firedb.session.rollback()


def test_indlæsning_af_lukket_punkt(firedb: FireDb, punkt: Punkt):
    """
    Test trigger BID#PUNKT.

    Direkte indlæsning af et lukket punkt er ikke tilladt, tjek at databasen
    brokker sig over det.
    """
    punkt._registreringtil = dt.datetime(2020, 9, 22, 13, 37)
    punkt._registreringfra = dt.datetime(2020, 9, 22, 13, 37)
    firedb.session.add(punkt)

    with pytest.raises(DatabaseError):
        firedb.session.commit()

    firedb.session.rollback()


def test_afregistrering_punktinfo(
    firedb: FireDb, sag: Sag, punkt: Punkt, punktinformationtype: PunktInformationType
):
    """
    Test trigger PUNKTINFO_TYPE_VALID_TRG - Automatisk afrestrering af tidligere punktinfo.
    """
    p1 = PunktInformation(
        punkt=punkt,
        infotype=punktinformationtype,
        _registreringfra=dt.datetime(2020, 9, 22, 19, 50),
    )
    se = Sagsevent(sag=sag, eventtype=EventType.PUNKTINFO_TILFOEJET)
    se.punktinformationer = [p1]
    firedb.session.add(se)
    firedb.session.commit()

    p2 = PunktInformation(
        punkt=punkt,
        infotype=punktinformationtype,
        _registreringfra=dt.datetime(2020, 9, 22, 19, 52),
    )
    se = Sagsevent(sag=sag, eventtype=EventType.PUNKTINFO_TILFOEJET)
    se.punktinformationer = [p2]
    firedb.session.add(se)
    firedb.session.commit()

    assert p1.registreringtil == p2.registreringfra
    assert p1.sagseventtilid == p2.sagseventfraid
    assert p2.registreringtil is None
    assert p2.sagseventtilid is None


def test_afregistrering_sagsinfo(firedb: FireDb, sag: Sag):
    """
    Test trigger BID#SAGSINFO - Automatisk afrestrering af tidligere sagsinfo.
    """
    si1 = Sagsinfo(
        sag=sag, behandler="B00001", beskrivelse="Første udgave", aktiv=Boolean.TRUE
    )

    firedb.session.add(si1)
    firedb.session.commit()

    si2 = Sagsinfo(
        sag=sag, behandler="B00001", beskrivelse="Første udgave", aktiv=Boolean.TRUE
    )
    firedb.session.add(si1)
    firedb.session.commit()

    assert si1.registreringtil == si2.registreringfra
    assert si2.registreringtil is None


def test_afregistrering_sagseventinfo(firedb: FireDb, sagsevent: Sagsevent):
    """
    Test trigger BID#SAGSEVENTINFO - Automatisk afrestrering af tidligere sagseventinfo.
    """
    si1 = SagseventInfo(sagsevent=sagsevent, beskrivelse="Første udgave")

    firedb.session.add(si1)
    firedb.session.commit()

    si2 = SagseventInfo(sagsevent=sagsevent, beskrivelse="Første udgave")
    firedb.session.add(si1)
    firedb.session.commit()

    assert si1.registreringtil == si2.registreringfra
    assert si2.registreringtil is None
