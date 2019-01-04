import pytest
from fireapi import FireDb
from fireapi.model import Sag, Sagsinfo


def test_hent_sag(firedb: FireDb, sag: Sag):
    s = firedb.hent_sag(sag.id)
    assert s.id is sag.id


def test_hent_alle_sager(firedb: FireDb):
    ss = firedb.hent_alle_sager()
    assert len(ss) > 1


def test_indset_sag(firedb: FireDb, guid):
    sagsinfo = Sagsinfo(aktiv="true", behandler="test")
    sag = Sag(id=guid, sagsinfos=[sagsinfo])
    firedb.indset_sag(sag)
