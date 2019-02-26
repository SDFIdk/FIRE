import datetime
from fireapi import FireDb
from fireapi.model import (
    Koordinat,
    Punkt,
    Observation,
    Beregning,
    Sagsevent,
    Sag,
    Srid,
    ObservationType,
)


def test_indset_beregning(firedb: FireDb, sag: Sag, punkt: Punkt, srid: Srid):
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
    beregning = Beregning()
    beregning.observationer.append(observation)
    koordinat = Koordinat(srid=srid, transformeret="false", punkt=punkt)
    beregning.koordinater.append(koordinat)
    firedb.indset_beregning(Sagsevent(sag=sag), beregning)

    assert koordinat.objectid is not None


def test_indset_beregning_invalidates_existing_koordinat(
    firedb: FireDb, sag: Sag, punkt: Punkt, srid: Srid
):
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
    beregning = Beregning()
    beregning.observationer.append(observation)
    koordinat = Koordinat(srid=srid, transformeret="false", punkt=punkt)
    beregning.koordinater.append(koordinat)
    firedb.indset_beregning(Sagsevent(sag=sag), beregning)

    # new beregning of the same observation with a new koordinat
    beregning2 = Beregning()
    beregning2.observationer.append(observation)
    koordinat2 = Koordinat(srid=srid, transformeret="false", punkt=punkt)
    beregning2.koordinater.append(koordinat2)
    firedb.indset_beregning(Sagsevent(sag=sag), beregning2)

    assert len(punkt.koordinater) == 2
    assert len([k for k in punkt.koordinater if k.registreringtil is None]) == 1
    assert koordinat2.srid is not None
