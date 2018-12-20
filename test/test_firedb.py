import uuid
import datetime
from fireapi import FireDb
from fireapi.model import (
    Sag,
    Sagsevent,
    Sagsinfo,
    Koordinat,
    Punkt,
    Observation,
    Beregning,
    Point,
    Geometry,
)

from fireapi.model.punkttyper import PunktInformationType


def test_has_session(firedb):
    assert hasattr(firedb, "session")


def test_utf8_roundtrip(firedb):
    utf8text = "æøåÆØÅ"
    newobject = PunktInformationType(
        infotype=str(uuid.uuid4()), anvendelse="TEKST", beskrivelse=utf8text
    )
    firedb.session.add(newobject)
    firedb.session.flush()

    roundtripped = (
        firedb.session.query(PunktInformationType)
        .filter(PunktInformationType.beskrivelse == utf8text)
        .one()
    )
    assert roundtripped is not None
    assert roundtripped.beskrivelse == utf8text


def test_hent_punkt(firedb):
    p = firedb.hent_punkt("7CA9F53D-DAE9-59C0-E053-1A041EAC5678")
    assert isinstance(p, Punkt)
    k = p.koordinater[0]
    assert isinstance(k, Koordinat)


def test_hent_alle_punkter(firedb):
    p = firedb.hent_alle_punkter()
    assert isinstance(p, list)


def test_hent_observationer(firedb):
    os = firedb.hent_observationer((1, 2))
    assert len(os) is 2

    os = firedb.hent_observationer((-999, -998))
    assert len(os) is 0


def test_hent_observationer_naer_opstillingspunkt(firedb):
    p = firedb.hent_punkt("7CA9F53D-DE26-59C0-E053-1A041EAC5678")
    os = firedb.hent_observationer_naer_opstillingspunkt(p, 100)
    assert len(os) is 2
    os = firedb.hent_observationer_naer_opstillingspunkt(
        p, 100, datetime.datetime(2015, 10, 8)
    )
    assert len(os) is 2
    os = firedb.hent_observationer_naer_opstillingspunkt(
        p, 100, datetime.datetime(2015, 11, 1)
    )
    assert len(os) is 1
    os = firedb.hent_observationer_naer_opstillingspunkt(p, 1000)
    assert len(os) is 4
    os = firedb.hent_observationer_naer_opstillingspunkt(
        p, 1000, datetime.datetime(2015, 10, 8)
    )
    assert len(os) is 4
    os = firedb.hent_observationer_naer_opstillingspunkt(
        p, 1000, datetime.datetime(2015, 10, 8), datetime.datetime(2015, 10, 9)
    )
    assert len(os) is 2


def test_hent_observationer_naer_geometri(firedb):
    go = firedb.hent_geometri_objekt("7CA9F53D-DE26-59C0-E053-1A041EAC5678")
    os = firedb.hent_observationer_naer_geometri(go.geometri, 10000)
    assert len(os) is 17
    point = Geometry("POINT (10.4811749340072 56.3061226484564)")
    os = firedb.hent_observationer_naer_geometri(point, 100)
    assert len(os) is 2
    polygon = Geometry(
        "POLYGON ((10.4811749340072 56.3061226484564, 10.5811749340072 56.3061226484564, 10.5811749340072 56.4061226484564, 10.4811749340072 56.4061226484564, 10.4811749340072 56.3061226484564))"
    )
    os = firedb.hent_observationer_naer_geometri(polygon, 100)
    assert len(os) is 6


def test_indset_sag(firedb: FireDb, guid):
    sagsinfo = Sagsinfo(aktiv="true", behandler="test")
    sag = Sag(id=guid, sagsinfos=[sagsinfo])
    firedb.indset_sag(sag)


def test_indset_observation(firedb: FireDb, sag: Sag, punkt: Punkt):
    observation = Observation(
        antal=0,
        observationstypeid="geometrisk_koteforskel",
        observationstidspunkt=datetime.datetime.utcnow(),
        opstillingspunkt=punkt,
        value1=0,
        value2=0,
        value3=0,
        value4=0,
        value5=0,
        value6=0,
        value7=0,
        value8=0,
    )
    firedb.indset_observation(sag, observation)


def test_indset_beregning(firedb: FireDb, sag: Sag, punkt: Punkt):
    observation = Observation(
        antal=0,
        observationstypeid="geometrisk_koteforskel",
        observationstidspunkt=datetime.datetime.utcnow(),
        opstillingspunkt=punkt,
        value1=0,
        value2=0,
        value3=0,
        value4=0,
        value5=0,
        value6=0,
        value7=0,
        value8=0,
    )
    firedb.indset_observation(sag, observation)
    beregning = Beregning()
    beregning.observationer.append(observation)
    koordinat = Koordinat(srid=-1, transformeret="false", punkt=punkt)
    beregning.koordinater.append(koordinat)
    firedb.indset_beregning(sag, beregning)
