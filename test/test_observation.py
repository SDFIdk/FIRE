import datetime as dt

import pytest

from fire.api import FireDb
from fire.api.model import (
    Sag,
    Sagsevent,
    SagseventInfo,
    Punkt,
    Observation,
    TrigonometriskKoteforskel,
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


def test_hent_observationer_fra_opstillingspunkt(firedb: FireDb):
    """
    Test udtræk af observationer til et givent opstillingspunkt.

    """
    pkt1 = firedb.hent_punkt("RDO1")
    pkt2 = firedb.hent_punkt("K-63-19113")
    pkt3 = firedb.hent_punkt("102-08-09067")

    # Kontroller at alle observationer hentes korrekt
    alle_obs = firedb.hent_observationer_fra_opstillingspunkt(pkt1)

    print(f"Antal observationer med RDO1 som opstillingspunkt: {len(alle_obs)}")
    assert len(alle_obs) == 16

    # Kontroller at alle observationer mellem opstillingspunkt og udvalgte
    # sigtepunkter hentes korrekt
    obs_til_sigtepunkter = firedb.hent_observationer_fra_opstillingspunkt(
        pkt1, sigtepunkter=[pkt2, pkt3]
    )
    for obs in obs_til_sigtepunkter:
        assert obs.sigtepunkt in (pkt2, pkt3)

    print(
        f"Antal observationer mellem RDO1 og (K-63-19113, 102-08-09067): {len(obs_til_sigtepunkter)}"
    )
    assert len(obs_til_sigtepunkter) == 6

    # Kontroller at tidsbegrænsning af søgningen fungerer som forventet
    fra = dt.datetime(2015, 1, 1)
    til = dt.datetime(2016, 12, 31)
    obs_periode = firedb.hent_observationer_fra_opstillingspunkt(
        pkt1,
        tid_fra=fra,
        tid_til=til,
    )
    print(
        f"Antal observationer fra RDO1 i perioden {fra} til {til}: {len(obs_periode)}"
    )
    for obs in obs_periode:
        assert obs.observationstidspunkt > fra and obs.observationstidspunkt < til

    # Udtræk kun specifikke observationstyper
    obs_trig = firedb.hent_observationer_fra_opstillingspunkt(
        pkt1, observationsklasse=TrigonometriskKoteforskel
    )
    print(f"Antal trigonometriske niv.-observationer fra RDO1: {len(obs_trig)}")
    assert len(obs_trig) == 2
    for obs in obs_trig:
        assert isinstance(obs, TrigonometriskKoteforskel)


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
    assert len(os) >= 68  # der KAN komme flere obs ved gentagende kørsler af tests
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
    assert len(os) >= 10  # der KAN komme flere obs ved gentagende kørsler af tests


def test_indset_observation(firedb: FireDb, sag: Sag, punkt: Punkt):
    obstype = firedb.session.query(ObservationsType).first()

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

    sagsevent = Sagsevent(sag=sag, id=uuid(), eventtype=EventType.OBSERVATION_INDSAT)
    sagseventtekst = "Ilægning af observation"
    sagseventinfo = SagseventInfo(beskrivelse=sagseventtekst)
    sagsevent.sagseventinfos.append(sagseventinfo)
    sagsevent.observationer = [obs1]

    firedb.indset_sagsevent(sagsevent)


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
        value1=1,
        value2=0,
        value3=0,
        value4=0,
        value5=0,
        value6=0,
        value7=0,
        value8=0,
    )

    firedb.indset_sagsevent(
        Sagsevent(
            sag=sag,
            eventtype=EventType.OBSERVATION_INDSAT,
            sagseventinfos=[
                SagseventInfo(beskrivelse="Testindsættelse af flere observationer")
            ],
            observationer=[obs1, obs2],
        )
    )


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


def test_fejlmeld_observation(
    firedb: FireDb, observation: Observation, sagsevent: Sagsevent
):
    firedb.session.commit()  # sikr at observationen er registreret i databasen
    assert observation.registreringtil is None
    assert observation.fejlmeldt == False

    firedb.fejlmeld_observation(observation, sagsevent)
    assert observation.registreringtil is not None
    assert observation.fejlmeldt == True
