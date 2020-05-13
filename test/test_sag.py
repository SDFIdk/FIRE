from fire.api import FireDb
from fire.api.model import Sag, Sagsinfo, Sagsevent, SagseventInfo, EventType


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
            sag=sag, eventtype=EventType.KOMMENTAR, sagseventinfos=[sagseventinfo],
        )
    )

    s = firedb.hent_sag(sag.id)
    assert s.sagsevents[0].sagseventinfos[0].beskrivelse == "Testing testing"
