import pytest

from fire.api import FireDb
from fire.api.model import (
    func,
    Koordinat,
    Punkt,
    Observation,
    Beregning,
    Sagsevent,
    SagseventInfo,
    Sag,
    Srid,
    ObservationsType,
    EventType,
)


def test_indset_beregning(
    firedb: FireDb,
    sag: Sag,
    sagsevent: Sagsevent,
    punkt: Punkt,
    srid: Srid,
    observationstype: ObservationsType,
):
    o0 = Observation(
        sagsevent=sagsevent,
        observationstidspunkt=func.current_timestamp(),
        observationstype=observationstype,
        opstillingspunkt=punkt,
    )

    firedb.indset_sagsevent(
        Sagsevent(
            sag=sag,
            sagseventinfos=[
                SagseventInfo(beskrivelse="Testindsættelse af observation")
            ],
            eventtype=EventType.OBSERVATION_INDSAT,
            observationer=[o0],
        )
    )
    beregning = Beregning()
    beregning.observationer.append(o0)
    koordinat = Koordinat(srid=srid, punkt=punkt, x=0, y=0, z=0, sx=0, sy=0, sz=0)
    beregning.koordinater.append(koordinat)

    firedb.indset_sagsevent(
        Sagsevent(
            sag=sag,
            eventtype=EventType.KOORDINAT_BEREGNET,
            sagseventinfos=[SagseventInfo(beskrivelse="Testberegning")],
            beregninger=[beregning],
            koordinater=beregning.koordinater,
        )
    )

    assert koordinat.objektid is not None


def test_indset_beregning_invalidates_existing_koordinat(
    firedb: FireDb, sag: Sag, punkt: Punkt, srid: Srid, observation: Observation
):
    firedb.indset_sagsevent(
        Sagsevent(
            sag=sag,
            sagseventinfos=[
                SagseventInfo(beskrivelse="Testindsættelse af observation")
            ],
            eventtype=EventType.OBSERVATION_INDSAT,
            observationer=[observation],
        )
    )
    beregning = Beregning()
    beregning.observationer.append(observation)
    koordinat = Koordinat(srid=srid, punkt=punkt, x=0, y=0, z=0, sx=0, sy=0, sz=0)
    beregning.koordinater.append(koordinat)

    firedb.indset_sagsevent(
        Sagsevent(
            sag=sag,
            eventtype=EventType.KOORDINAT_BEREGNET,
            sagseventinfos=[SagseventInfo(beskrivelse="Testberegning")],
            beregninger=[beregning],
            koordinater=beregning.koordinater,
        )
    )

    # new beregning of the same observation with a new koordinat
    beregning2 = Beregning()
    beregning2.observationer.append(observation)
    koordinat2 = Koordinat(
        srid=srid,
        punkt=punkt,
        x=1,
        y=0,
        z=0,
        sx=0,
        sy=0,
        sz=0,
    )
    beregning2.koordinater.append(koordinat2)

    firedb.indset_sagsevent(
        Sagsevent(
            sag=sag,
            eventtype=EventType.KOORDINAT_BEREGNET,
            sagseventinfos=[SagseventInfo(beskrivelse="Testberegning")],
            beregninger=[beregning2],
            koordinater=beregning2.koordinater,
        )
    )

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
