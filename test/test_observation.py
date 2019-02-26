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
    ObservationType,
)


def test_observation(firedb: FireDb, observation: Observation):
    firedb.session.commit()
    o1 = firedb.session.query(Observation).get(observation.objectid)
    assert o1.objectid == observation.objectid


def test_hent_observationer(firedb: FireDb):
    os = firedb.hent_observationer((1, 2))
    assert len(os) is 2
    os = firedb.hent_observationer((-999, -998))
    assert len(os) is 0


def test_hent_observationer_naer_opstillingspunkt(firedb: FireDb):
    p = firedb.hent_punkt("814E9044-1AAB-5A4E-E053-1A041EACF9E4")
    os = firedb.hent_observationer_naer_opstillingspunkt(p, 100)
    assert len(os) is 32
    os = firedb.hent_observationer_naer_opstillingspunkt(
        p, 100, datetime.datetime(2015, 10, 8)
    )
    assert len(os) is 12
    os = firedb.hent_observationer_naer_opstillingspunkt(
        p, 100, datetime.datetime(2016, 11, 1)
    )
    assert len(os) is 6
    os = firedb.hent_observationer_naer_opstillingspunkt(p, 1000)
    assert len(os) is 34
    os = firedb.hent_observationer_naer_opstillingspunkt(
        p, 1000, datetime.datetime(2015, 10, 8)
    )
    assert len(os) is 12
    os = firedb.hent_observationer_naer_opstillingspunkt(
        p, 1000, datetime.datetime(2015, 10, 8), datetime.datetime(2016, 10, 9)
    )
    assert len(os) is 6


def test_hent_observationer_naer_geometri(firedb: FireDb):
    go = firedb.hent_geometri_objekt("814E9044-1AAB-5A4E-E053-1A041EACF9E4")
    os = firedb.hent_observationer_naer_geometri(go.geometri, 10000)
    assert len(os) is 46
    point = Geometry("POINT (10.4811749340072 56.3061226484564)")
    os = firedb.hent_observationer_naer_geometri(point, 100)
    assert len(os) is 2
    polygon = Geometry(
        "POLYGON ((10.4811749340072 56.3061226484564, 10.5811749340072 56.3061226484564, 10.5811749340072 56.4061226484564, 10.4811749340072 56.4061226484564, 10.4811749340072 56.3061226484564))"
    )
    os = firedb.hent_observationer_naer_geometri(polygon, 100)
    assert len(os) is 6


def test_indset_observation(firedb: FireDb, sag: Sag, punkt: Punkt):
    obstype = firedb.session.query(ObservationType).first()
    observation = Observation(
        antal=0,
        observationstype=obstype,
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
    firedb.indset_observation(Sagsevent(sag=sag), observation)
