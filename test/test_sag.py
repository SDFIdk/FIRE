import os
from typing import Callable

import pytest

import fire
from fire.api import FireDb
from fire.api.model import (
    Punkt,
    Sag,
    Sagsinfo,
    Sagsevent,
    SagseventInfo,
    SagseventInfoMateriale,
    EventType,
)


def test_hent_sag(firedb: FireDb, sag: Sag):
    s = firedb.hent_sag(sag.id)
    assert s.id is sag.id


def test_hent_alle_sager(firedb: FireDb):
    ss = firedb.hent_alle_sager()
    assert len(ss) > 1


def test_indset_sag(firedb: FireDb):
    sagsinfo = Sagsinfo(aktiv="true", behandler="test")
    sag = Sag(sagsinfos=[sagsinfo])
    firedb.indset_sag(sag)


def test_indset_sagsevent(firedb: FireDb, sag: Sag):
    sagseventinfo = SagseventInfo(beskrivelse="Testing testing")
    firedb.indset_sagsevent(
        Sagsevent(
            sag=sag,
            eventtype=EventType.KOMMENTAR,
            sagseventinfos=[sagseventinfo],
        )
    )

    s = firedb.hent_sag(sag.id)
    assert s.sagsevents[0].sagseventinfos[0].beskrivelse == "Testing testing"


def test_indset_sagsevent_materiale(firedb: FireDb, sag: Sag):

    blob = os.urandom(1000)

    sagseventinfo = SagseventInfo(
        beskrivelse="Testing testing",
        materialer=[SagseventInfoMateriale(materiale=blob)],
    )
    firedb.indset_sagsevent(
        Sagsevent(
            sag=sag,
            eventtype=EventType.KOMMENTAR,
            sagseventinfos=[sagseventinfo],
        )
    )

    s = firedb.hent_sag(sag.id)
    assert s.sagsevents[0].sagseventinfos[0].materialer[0].materiale == blob


def test_indset_sagsevent(firedb: FireDb, sag: Sag):
    sagseventinfo = SagseventInfo(beskrivelse="Testing testing")
    firedb.indset_sagsevent(
        Sagsevent(
            sag=sag,
            eventtype=EventType.KOMMENTAR,
            sagseventinfos=[sagseventinfo],
        )
    )

    s = firedb.hent_sag(sag.id)
    assert s.sagsevents[0].sagseventinfos[0].beskrivelse == "Testing testing"


def test_luk_sag(firedb: FireDb, sag: Sag):
    assert sag.aktiv is True
    firedb.luk_sag(sag)
    s = firedb.hent_sag(sag.id)
    assert s.aktiv is False

    with pytest.raises(TypeError):
        firedb.luk_sag(4242)


def test_ny_sag(firedb: FireDb):
    """
    Test FireDb.ny_sag()
    """
    sag = firedb.ny_sag("teste testesen", "sag til test")

    assert sag.id is not None
    assert sag.registreringfra is not None
    assert sag.behandler == "teste testesen"

    firedb.session.rollback()


def test_ny_sagsevent(firedb: FireDb, sag: Sag, punktfabrik: Callable):
    """
    Test 'simple' inputs til Sag.ny_sagsevent()
    """

    # Indsættelse af punkt tester scenarie hvor kun "obligatorisk"
    # data for en eventtype er tilgængeligt.
    punkt = punktfabrik()
    sagsevent = sag.ny_sagsevent(
        beskrivelse="tests",
        punkter=[punkt],
    )

    # Sikr at id er tildelt før flush()
    assert sagsevent.id is not None

    firedb.indset_sagsevent(sagsevent, commit=False)
    firedb.session.flush()

    assert sagsevent.sag == sag
    assert sagsevent.id is not None
    assert sagsevent.eventtype == EventType.PUNKT_OPRETTET
    assert sagsevent.beskrivelse == "tests"

    # Indsættelse af punkt+geometriobjekt tester scenarie hvor både "obligatorisk"
    # og "valgfri" data for en eventtype er tilgængeligt.
    punkt = punktfabrik()
    sagsevent = sag.ny_sagsevent(
        beskrivelse="tests",
        punkter=[punkt],
        geometriobjekter=[punkt.geometriobjekter[0]],
    )

    # Sikr at id er tildelt før flush()
    assert sagsevent.id is not None

    firedb.indset_sagsevent(sagsevent, commit=False)
    firedb.session.flush()

    assert sagsevent.sag == sag
    assert sagsevent.id is not None
    assert sagsevent.eventtype == EventType.PUNKT_OPRETTET
    assert sagsevent.beskrivelse == "tests"

    uuid = fire.uuid()
    sagseventid = sag.ny_sagsevent(
        beskrivelse="kommentar",
        id=uuid,
    )

    assert sagseventid.id == uuid
    firedb.indset_sagsevent(sagseventid, commit=False)
    firedb.session.flush()
    assert sagseventid.id == uuid

    firedb.session.rollback()


def test_ny_sagsevent_data(firedb: FireDb, sag: Sag, punktfabrik: Callable):
    """
    Test indsættelse af data direkte med Sag.ny_sagsevent().
    """
    punkter = [punktfabrik() for _ in range(5)]
    sagsevent = sag.ny_sagsevent(
        beskrivelse="tests",
        punkter=punkter,
    )
    firedb.indset_sagsevent(sagsevent, commit=False)
    firedb.session.flush()

    assert len(sagsevent.punkter) == len(punkter)
    assert punkter[0].sagsevent.id == sagsevent.id
    assert sagsevent.punkter[0] == punkter[0]
    assert punkter[0].id is not None

    firedb.session.rollback()


def test_ny_sagsevent_materiale(firedb: FireDb, sag: Sag):
    """
    Test tilknyttelse af materiale til et sagsevent.
    """

    html = "<html><title>Test</test><body>This is a test</body></html>"
    blob = os.urandom(1000)

    sagsevent = sag.ny_sagsevent(
        beskrivelse="Indsæt materiale",
        htmler=[html],
        materialer=[blob],
    )
    firedb.indset_sagsevent(sagsevent, commit=False)
    firedb.session.flush()

    assert sagsevent.sagseventinfos[0].materialer[0].materiale == blob
    assert sagsevent.sagseventinfos[0].htmler[0].html == html

    firedb.session.rollback()


def test_ny_sagsevent_ukendt(firedb: FireDb, sag: Sag):
    """
    Test at der fejles retmæssigt ved forsøg på tilknyttelse af ukendte
    objekttyper til Sagsevent.
    """

    with pytest.raises(ValueError):
        sag.ny_sagsevent(
            beskrivelse="Test tilknytning af ukendt objekttype",
            kafferkopper=["kaffe", "kop", "kendes", "ikke"],
        )


def test_ny_sagsevent_slettede(firedb: FireDb, sag: Sag, koordinatfabrik: Callable):
    """
    Test at slettede objekter afregistreres korrekt når `Sag.ny_sagsevent()`
    benyttes.
    """
    koordinater = [koordinatfabrik() for _ in range(5)]

    sagsevent = sag.ny_sagsevent(
        beskrivelse="tests",
        koordinater=koordinater,
    )

    firedb.indset_sagsevent(sagsevent, commit=False)
    firedb.session.flush()

    sagsevent_slettede = sag.ny_sagsevent(
        beskrivelse="Fjern punkter igen",
        koordinater_slettede=koordinater,
    )

    firedb.indset_sagsevent(sagsevent_slettede, commit=False)
    firedb.session.flush()

    for i in range(5):
        assert koordinater[i].registreringtil is not None
