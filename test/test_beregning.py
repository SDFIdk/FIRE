import datetime
from fireapi import FireDb
from fireapi.model import Sag, Koordinat, Punkt, Observation, Beregning


def test_beregning(firedb: FireDb, beregning: Beregning):
    firedb.session.commit()

    b0 = firedb.session.query(Beregning).get(beregning.objectid)

    assert b0.objectid == beregning.objectid

    assert len(b0.observationer) == 2

    assert b0.observationer[0].beregninger[0].objectid == beregning.objectid


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
