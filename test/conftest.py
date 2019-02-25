import pytest
import os
import uuid
from fireapi import FireDb
from fireapi.model import (
    func,
    RegisteringTidObjekt,
    Sag,
    Punkt,
    GeometriObjekt,
    Observation,
    ObservationType,
    Bbox,
    Sagsevent,
    Sagsinfo,
    Beregning,
    Koordinat,
    EventType,
)

user = os.environ.get("ORA_USER") or "fire"
password = os.environ.get("ORA_PASSWORD") or "fire"
host = os.environ.get("ORA_HOST") or "localhost"
port = os.environ.get("ORA_PORT") or "1521"
db = os.environ.get("ORA_db") or "xe"


@pytest.fixture
def firedb():
    return FireDb(f"{user}:{password}@{host}:{port}/{db}", debug=True)


@pytest.fixture()
def guid():
    return str(uuid.uuid4())


@pytest.fixture()
def sag(firedb, guid):
    s0 = Sag(id=guid)
    si0 = Sagsinfo(sag=s0, aktiv="true", behandler="yyy")
    firedb.session.add(si0)
    # s0 = Sag(id=guid, sagstype="dummy", behandler="yyy")
    firedb.session.add(s0)
    firedb.session.flush()
    return s0


@pytest.fixture()
def sagsevent(firedb, sag, guid):
    e0 = Sagsevent(id=guid, sag=sag, eventtype=EventType.KOMMENTAR)
    firedb.session.add(e0)
    return e0


@pytest.fixture()
def punkt(firedb, sagsevent, guid):
    sagsevent.eventtype = EventType.PUNKT_OPRETTET
    p0 = Punkt(id=guid, sagsevent=sagsevent)
    firedb.session.add(p0)
    return p0


@pytest.fixture()
def koordinat(firedb, sagsevent, punkt, srid):
    sagsevent.eventtype = EventType.KOORDINAT_BEREGNET
    k0 = Koordinat(sagsevent=sagsevent, punkt=punkt, transformeret="true", srid=srid)
    firedb.session.add(k0)
    return k0


@pytest.fixture()
def observationstype(firedb):
    ot0 = firedb.session.query(ObservationType).first()
    return ot0


@pytest.fixture()
def observation(firedb, sagsevent, observationstype, punkt):
    sagsevent.eventtype = EventType.OBSERVATION_INDSAT
    o0 = Observation(
        sagsevent=sagsevent,
        value1=0,
        value2=0,
        value3=0,
        value4=0,
        value5=0,
        value6=0,
        value7=0,
        value8=0,
        value9=0,
        value10=0,
        value11=0,
        value12=0,
        value13=0,
        value14=0,
        value15=0,
        antal=0,
        observationstidspunkt=func.sysdate(),
        observationstype=observationstype,
        opstillingspunkt=punkt,
        sigtepunkt=punkt,
    )
    firedb.session.add(o0)
    return o0


@pytest.fixture()
def observationer(firedb, sagsevent, observationstype, punkt):
    sagsevent.eventtype = EventType.OBSERVATION_INDSAT
    o0 = Observation(
        sagsevent=sagsevent,
        value1=0,
        value2=0,
        value3=0,
        value4=0,
        value5=0,
        value6=0,
        value7=0,
        value8=0,
        value9=0,
        value10=0,
        value11=0,
        value12=0,
        value13=0,
        value14=0,
        value15=0,
        antal=0,
        observationstidspunkt=func.sysdate(),
        observationstype=observationstype,
        opstillingspunkt=punkt,
        sigtepunkt=punkt,
    )
    o1 = Observation(
        sagsevent=sagsevent,
        value1=0,
        value2=0,
        value3=0,
        value4=0,
        value5=0,
        value6=0,
        value7=0,
        value8=0,
        value9=0,
        value10=0,
        value11=0,
        value12=0,
        value13=0,
        value14=0,
        value15=0,
        antal=0,
        observationstidspunkt=func.sysdate(),
        observationstype=observationstype,
        opstillingspunkt=punkt,
        sigtepunkt=punkt,
    )
    firedb.session.add(o0)
    firedb.session.add(o1)
    return [o0, o1]


@pytest.fixture()
def beregning(firedb, sagsevent, observationer):
    sagsevent.eventtype = EventType.KOORDINAT_BEREGNET
    b0 = Beregning(sagsevent=sagsevent, observationer=observationer)
    firedb.session.add(b0)
    return b0


@pytest.fixture()
def srid(firedb):
    return firedb.hent_srider()[0]


@pytest.fixture()
def punktinformationtype(firedb):
    return firedb.hent_punktinformationtyper()[0]
