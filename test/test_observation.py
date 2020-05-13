import datetime as dt

from fire.api import FireDb
from fire.api.model import (
    Sag,
    Sagsevent,
    Punkt,
    Observation,
    Geometry,
    ObservationType,
)


def test_observation(firedb: FireDb, observation: Observation):
    firedb.session.commit()
    o1 = firedb.session.query(Observation).get(observation.objectid)
    assert o1.objectid == observation.objectid


def test_hent_observationer(firedb: FireDb, observationer):
    firedb.session.commit()
    id1 = observationer[0].objectid
    id2 = observationer[1].objectid
    os = firedb.hent_observationer((id1, id2))
    assert len(os) == 2
    os = firedb.hent_observationer((-999, -998))
    assert len(os) == 0


def test_hent_observationer_naer_opstillingspunkt(firedb: FireDb):
    p = firedb.hent_punkt("67e3987a-dc6b-49ee-8857-417ef35777af")
    os = firedb.hent_observationer_naer_opstillingspunkt(p, 100)
    assert len(os) == 6
    os = firedb.hent_observationer_naer_opstillingspunkt(
        p, 100, dt.datetime(2015, 11, 1)
    )
    assert len(os) == 6
    os = firedb.hent_observationer_naer_opstillingspunkt(
        p, 100, dt.datetime(2019, 2, 1)
    )
    assert len(os) == 3
    os = firedb.hent_observationer_naer_opstillingspunkt(p, 1000)
    assert len(os) == 22
    os = firedb.hent_observationer_naer_opstillingspunkt(
        p, 1000, dt.datetime(2019, 2, 1)
    )
    assert len(os) == 11
    os = firedb.hent_observationer_naer_opstillingspunkt(
        p, 1000, dt.datetime(2015, 11, 1), dt.datetime(2016, 11, 1)
    )
    assert len(os) == 11


def test_hent_observationer_naer_geometri(firedb: FireDb):
    go = firedb.hent_geometri_objekt(punktid="67e3987a-dc6b-49ee-8857-417ef35777af")
    os = firedb.hent_observationer_naer_geometri(go.geometri, 10000)
    assert len(os) == 68
    point = Geometry("POINT (10.2112609352788 56.1567354902778)")
    os = firedb.hent_observationer_naer_geometri(point, 100)
    assert len(os) == 6
    polygon = Geometry(
        (
            "POLYGON ((10.209 56.155, "
            "10.209 56.158, "
            "10.215 56.158, "
            "10.215 56.155, "
            "10.209 56.155))"
        )
    )
    os = firedb.hent_observationer_naer_geometri(polygon, 100)
    assert len(os) == 10


def test_indset_observation(firedb: FireDb, sag: Sag, punkt: Punkt):
    obstype = firedb.session.query(ObservationType).first()
    observation = Observation(
        antal=0,
        observationstype=obstype,
        observationstidspunkt=dt.datetime.utcnow(),
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
