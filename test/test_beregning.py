import datetime
from fireapi import FireDb
from fireapi.model import Sag, Koordinat, Punkt, Observation, Beregning


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


def test_indset_beregning_invalidates_existing_koordinat(
    firedb: FireDb, sag: Sag, punkt: Punkt
):
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
    koordinat = Koordinat(srid="-1", transformeret="false", punkt=punkt)
    beregning.koordinater.append(koordinat)
    firedb.indset_beregning(sag, beregning)

    # new beregning of the same observation with a new koordinat
    beregning2 = Beregning()
    beregning2.observationer.append(observation)
    koordinat2 = Koordinat(srid="-1", transformeret="false", punkt=punkt)
    beregning2.koordinater.append(koordinat2)
    firedb.indset_beregning(sag, beregning2)

    assert len(punkt.koordinater) == 2
    assert len([k for k in punkt.koordinater if k.registreringtil is None]) == 1
