import pytest

from fire.api import FireDb
from fire.api.model import (
    func,
    Koordinat,
    Punkt,
    Observation,
    Beregning,
    Sagsevent,
    Sag,
    Srid,
    ObservationType,
    EventType,
)


def test_indset_beregning(
    firedb: FireDb,
    sag: Sag,
    sagsevent: Sagsevent,
    punkt: Punkt,
    srid: Srid,
    observationstype: ObservationType,
):
    o0 = Observation(
        sagsevent=sagsevent,
        observationstidspunkt=func.sysdate(),
        observationstype=observationstype,
        opstillingspunkt=punkt,
    )

    firedb.indset_observation(Sagsevent(sag=sag), o0)
    beregning = Beregning()
    beregning.observationer.append(o0)
    koordinat = Koordinat(
        srid=srid, transformeret="false", punkt=punkt, x=0, y=0, z=0, sx=0, sy=0, sz=0
    )
    beregning.koordinater.append(koordinat)
    firedb.indset_beregning(Sagsevent(sag=sag), beregning)

    assert koordinat.objectid is not None


def test_indset_beregning_invalidates_existing_koordinat(
    firedb: FireDb, sag: Sag, punkt: Punkt, srid: Srid, observation: Observation
):
    firedb.indset_observation(Sagsevent(sag=sag), observation)
    beregning = Beregning()
    beregning.observationer.append(observation)
    koordinat = Koordinat(
        srid=srid, transformeret="false", punkt=punkt, x=0, y=0, z=0, sx=0, sy=0, sz=0
    )
    beregning.koordinater.append(koordinat)
    firedb.indset_beregning(Sagsevent(sag=sag), beregning)

    # new beregning of the same observation with a new koordinat
    beregning2 = Beregning()
    beregning2.observationer.append(observation)
    koordinat2 = Koordinat(
        srid=srid, transformeret="false", punkt=punkt, x=1, y=0, z=0, sx=0, sy=0, sz=0,
    )
    beregning2.koordinater.append(koordinat2)
    firedb.indset_beregning(Sagsevent(sag=sag), beregning2)

    assert len(punkt.koordinater) == 2
    assert len([k for k in punkt.koordinater if k.registreringtil is None]) == 1
    assert koordinat2.srid is not None


def test_luk_beregning(firedb: FireDb, beregning: Beregning, sagsevent: Sagsevent):
    firedb.session.commit()
    assert beregning.registreringtil is None
    assert beregning.sagsevent.eventtype == EventType.KOORDINAT_BEREGNET

    firedb.luk_beregning(beregning, sagsevent)
    assert beregning.registreringtil is not None
    assert beregning.sagsevent.eventtype == EventType.KOORDINAT_NEDLAGT
    for koordinat in beregning.koordinater:
        assert koordinat.registreringtil is not None
        assert koordinat.sagsevent.eventtype == EventType.KOORDINAT_NEDLAGT

    with pytest.raises(TypeError):
        firedb.luk_beregning(234)
