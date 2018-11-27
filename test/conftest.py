import pytest
import os
import uuid
from fireapi import FireDb
from fireapi.model import *

user = os.environ.get("ORA_USER") or "fire"
password = os.environ.get("ORA_PASSWORD") or "fire"
host = os.environ.get("ORA_HOST") or "localhost"
port = os.environ.get("ORA_PORT") or "1521"
db = os.environ.get("ORA_db") or "xe"


@pytest.fixture(scope="session")
def firedb():
    return FireDb(f"{user}:{password}@{host}:{port}/{db}")

@pytest.fixture()
def guid():
    return str(uuid.uuid4())

@pytest.fixture()
def sag(firedb, guid):
    s0 = Sag(id=guid)
    #s0 = Sag(id=guid, sagstype="dummy", behandler="yyy")
    firedb.session.add(s0)
    return s0

@pytest.fixture()
def sagsevent(firedb, sag, guid):
    e0 = Sagsevent(id=guid, sag=sag, event="dummy")
    firedb.session.add(e0)
    return e0

@pytest.fixture()
def punkt(firedb, sagsevent, guid):
    p0 = Punkt(id=guid, sagsevent=sagsevent)
    firedb.session.add(p0)
    return p0

@pytest.fixture()
def koordinat(firedb, sagsevent, punkt):
    k0 = Koordinat(sagsevent=sagsevent, punkt=punkt, transformeret="true", srid="-1")
    firedb.session.add(k0)
    return k0

@pytest.fixture()
def observationstype(firedb):
    ot0 = ObservationType(observationstype="test", beskrivelse="test", value1="test", sigtepunktid='true')
    firedb.session.add(ot0)
    return ot0

@pytest.fixture()
def observation(firedb, sagsevent, observationstype, punkt):
    o0 = Observation(
        sagsevent=sagsevent,
        value1=0,
        antal=0,
        observationstidspunkt=func.sysdate(),
        observationstype=observationstype,
        opstillingspunkt=punkt,
        sigtepunkt=punkt)
    firedb.session.add(o0)
    return o0

