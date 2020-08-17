import datetime as dt

import pytest

from fire.api import FireDb
from fire.api.model import (
    Sag,
    Sagsevent,
    SagseventInfo,
    Punkt,
    Observation,
    Geometry,
    ObservationsType,
    EventType,
)
from fire import uuid


def test_observation(firedb: FireDb, observation: Observation):
    firedb.session.commit()
    o1 = firedb.session.query(Observation).get(observation.objektid)
    assert o1.objektid == observation.objektid


def test_hent_observationer(firedb: FireDb, observationer):
    firedb.session.commit()
    id1 = observationer[0].id
    id2 = observationer[1].id
    os = firedb.hent_observationer((id1, id2))
    assert len(os) == 2
    os = firedb.hent_observationer(
        ("60cd07f2-2c9a-471c-bc7e-ef3473098e85", "7e277296-2412-46ff-91f2-0841cf1cc3af")
    )
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
    obstype = firedb.session.query(ObservationsType).first()

    sagsevent = Sagsevent(sag=sag, id=uuid(), eventtype=EventType.OBSERVATION_INDSAT)
    sagseventtekst = "Ilægning af observation"
    sagseventinfo = SagseventInfo(beskrivelse=sagseventtekst)
    sagsevent.sagseventinfos.append(sagseventinfo)

    obs1 = Observation(
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

    firedb.indset_observation(sagsevent, obs1)


def test_indset_flere_observationer(firedb: FireDb, sag: Sag, punkt: Punkt):
    obstype = firedb.session.query(ObservationsType).first()

    sagsevent = Sagsevent(sag=sag, id=uuid(), eventtype=EventType.OBSERVATION_INDSAT)
    sagseventtekst = "Ilægning af flere observationer"
    sagseventinfo = SagseventInfo(beskrivelse=sagseventtekst)
    sagsevent.sagseventinfos.append(sagseventinfo)

    obs1 = Observation(
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

    obs2 = Observation(
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

    firedb.indset_flere_observationer(sagsevent, [obs1, obs2])


def test_luk_observation(
    firedb: FireDb, observation: Observation, sagsevent: Sagsevent
):
    firedb.session.commit()
    assert observation.registreringtil is None
    assert observation.sagsevent.eventtype == EventType.OBSERVATION_INDSAT

    firedb.luk_observation(observation, sagsevent)
    assert observation.registreringtil is not None
    assert observation.sagsevent.eventtype == EventType.OBSERVATION_NEDLAGT

    with pytest.raises(TypeError):
        firedb.luk_observation(9999)
